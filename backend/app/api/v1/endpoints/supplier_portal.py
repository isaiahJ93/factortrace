# app/api/v1/endpoints/supplier_portal.py
"""
Supplier Portal API Endpoints.

Provides supplier-facing endpoints for:
- Checkout: Pay for reports via Stripe
- Reports: List and download completed reports
- Sessions: View wizard session history

This implements the supplier self-serve flow:
1. Pay → 2. Complete wizard → 3. Get report emailed → 4. Download again anytime
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.auth_schemas import CurrentUser
from app.models.wizard import ComplianceWizardSession, WizardStatus
from app.models.voucher import Voucher
from app.services.stripe_checkout import (
    create_checkout_session,
    get_checkout_session_status,
    handle_checkout_complete,
    verify_webhook_signature,
    PRODUCTS,
)
from app.services.email_service import get_email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portal", tags=["Supplier Portal"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class CheckoutRequest(BaseModel):
    """Request to create a checkout session."""
    email: EmailStr = Field(..., description="Supplier email address")
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name")
    product: str = Field(default="csrd_report", description="Product to purchase")
    success_url: str = Field(..., description="URL to redirect after payment")
    cancel_url: str = Field(..., description="URL to redirect if cancelled")


class CheckoutResponse(BaseModel):
    """Response from checkout session creation."""
    checkout_url: str
    session_id: str


class CheckoutStatusResponse(BaseModel):
    """Status of a checkout session."""
    id: str
    status: str
    payment_status: str
    customer_email: Optional[str] = None


class ProductInfo(BaseModel):
    """Available product information."""
    id: str
    name: str
    description: str
    price_cents: int
    currency: str


class SupplierReportSummary(BaseModel):
    """Summary of a completed supplier report."""
    id: int
    session_id: int
    company_name: str
    reporting_year: int
    total_tco2e: float
    scope1_tco2e: float
    scope2_tco2e: float
    scope3_tco2e: float
    completed_at: datetime
    pdf_url: Optional[str] = None
    xbrl_url: Optional[str] = None


class SupplierSessionSummary(BaseModel):
    """Summary of a wizard session for supplier view."""
    id: int
    status: str
    current_step: str
    company_name: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_tco2e: Optional[float] = None


# =============================================================================
# PUBLIC ENDPOINTS (NO AUTH)
# =============================================================================

@router.get("/products", response_model=List[ProductInfo])
async def list_products():
    """
    List available products for purchase.

    Returns available report products with pricing.
    """
    return [
        ProductInfo(
            id=product_id,
            name=config["name"],
            description=config["description"],
            price_cents=config["price_cents"],
            currency=config["currency"],
        )
        for product_id, config in PRODUCTS.items()
    ]


@router.post("/checkout", response_model=CheckoutResponse)
async def create_supplier_checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db),
):
    """
    Create a Stripe checkout session for supplier purchase.

    This is the entry point for the supplier self-serve flow.
    After payment, a voucher is created and wizard session auto-starts.
    """
    try:
        checkout_url, session_id = create_checkout_session(
            db,
            email=request.email,
            company_name=request.company_name,
            product=request.product,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )

        return CheckoutResponse(
            checkout_url=checkout_url,
            session_id=session_id,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/checkout/{session_id}/status", response_model=CheckoutStatusResponse)
async def get_checkout_status(session_id: str):
    """
    Get status of a checkout session.

    Use this to check if payment has completed after redirect.
    """
    try:
        status = get_checkout_session_status(session_id)
        return CheckoutStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting checkout status: {e}")
        raise HTTPException(status_code=404, detail="Checkout session not found")


@router.post("/webhook/stripe")
async def handle_stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handle Stripe webhooks.

    Processes checkout.session.completed events to:
    1. Create voucher
    2. Auto-start wizard session
    3. Send confirmation email
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook_signature(payload, sig_header)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle checkout completion
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        voucher, wizard_session = handle_checkout_complete(
            db,
            stripe_session_id=session["id"],
        )

        if voucher:
            # Send confirmation email
            email_service = get_email_service()
            await email_service.send_voucher_email(
                to_email=voucher.company_email,
                company_name=voucher.company_name,
                voucher_code=voucher.code,
                valid_until=voucher.valid_until,
                wizard_url=f"https://app.factortrace.com/wizard/{wizard_session.id}",
            )

            logger.info(
                f"Checkout complete: voucher={voucher.code}, "
                f"session={wizard_session.id}"
            )

    return {"status": "ok"}


# =============================================================================
# AUTHENTICATED ENDPOINTS (SUPPLIER AUTH)
# =============================================================================

@router.get("/my-sessions", response_model=List[SupplierSessionSummary])
async def list_my_sessions(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List wizard sessions for the current supplier.

    Returns all sessions created by this supplier's tenant.
    """
    query = (
        db.query(ComplianceWizardSession)
        .filter(ComplianceWizardSession.tenant_id == current_user.tenant_id)
    )

    if status:
        try:
            status_enum = WizardStatus(status)
            query = query.filter(ComplianceWizardSession.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    sessions = (
        query
        .order_by(ComplianceWizardSession.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for session in sessions:
        company_name = None
        total_tco2e = None

        if session.company_profile:
            company_name = session.company_profile.get("name")

        if session.calculated_emissions:
            total_tco2e = session.calculated_emissions.get("total_tco2e")

        results.append(SupplierSessionSummary(
            id=session.id,
            status=session.status.value,
            current_step=session.current_step,
            company_name=company_name,
            created_at=session.created_at,
            completed_at=session.completed_at,
            total_tco2e=total_tco2e,
        ))

    return results


@router.get("/my-reports", response_model=List[SupplierReportSummary])
async def list_my_reports(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List completed reports for the current supplier.

    Returns all completed wizard sessions with emissions data.
    """
    sessions = (
        db.query(ComplianceWizardSession)
        .filter(
            ComplianceWizardSession.tenant_id == current_user.tenant_id,
            ComplianceWizardSession.status == WizardStatus.COMPLETED,
        )
        .order_by(ComplianceWizardSession.completed_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for session in sessions:
        if not session.calculated_emissions:
            continue

        company_profile = session.company_profile or {}
        emissions = session.calculated_emissions

        results.append(SupplierReportSummary(
            id=session.report_id or session.id,
            session_id=session.id,
            company_name=company_profile.get("name", "Unknown"),
            reporting_year=company_profile.get("reporting_year", 2024),
            total_tco2e=emissions.get("total_tco2e", 0),
            scope1_tco2e=emissions.get("scope1_tco2e", 0),
            scope2_tco2e=emissions.get("scope2_tco2e", 0),
            scope3_tco2e=emissions.get("scope3_tco2e", 0),
            completed_at=session.completed_at or session.updated_at,
            pdf_url=f"/api/v1/portal/my-reports/{session.id}/download?format=pdf",
            xbrl_url=f"/api/v1/portal/my-reports/{session.id}/download?format=xbrl",
        ))

    return results


@router.get("/my-reports/{session_id}/download")
async def download_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    format: str = Query("pdf", pattern="^(pdf|xbrl|json)$"),
):
    """
    Download a completed report.

    Supports PDF, XBRL/iXBRL, and JSON formats.
    """
    # Get session with tenant isolation
    session = (
        db.query(ComplianceWizardSession)
        .filter(
            ComplianceWizardSession.id == session_id,
            ComplianceWizardSession.tenant_id == current_user.tenant_id,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Report not found")

    if session.status != WizardStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report not yet completed")

    if not session.calculated_emissions:
        raise HTTPException(status_code=400, detail="No emissions data available")

    # Build response based on format
    company_profile = session.company_profile or {}
    emissions = session.calculated_emissions

    if format == "json":
        # Return raw JSON data
        return {
            "session_id": session.id,
            "company_profile": company_profile,
            "emissions": emissions,
            "methodology": emissions.get("methodology_notes"),
            "generated_at": session.completed_at.isoformat() if session.completed_at else None,
        }

    elif format == "pdf":
        # For PDF, return redirect to report generation endpoint
        # In production, this would return actual PDF file or S3 URL
        return {
            "status": "redirect",
            "message": "PDF generation in progress",
            "download_url": f"/api/v1/wizard/sessions/{session_id}/generate-report?format=pdf",
        }

    elif format == "xbrl":
        # For XBRL, return redirect to report generation endpoint
        return {
            "status": "redirect",
            "message": "XBRL generation in progress",
            "download_url": f"/api/v1/wizard/sessions/{session_id}/generate-report?format=xhtml",
        }

    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


@router.get("/my-vouchers")
async def list_my_vouchers(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = Query(50, le=100),
):
    """
    List vouchers for the current supplier.

    Returns active and used vouchers.
    """
    vouchers = (
        db.query(Voucher)
        .filter(Voucher.tenant_id == current_user.tenant_id)
        .order_by(Voucher.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": v.id,
            "code": v.code,
            "status": v.status.value if v.status else "unknown",
            "company_name": v.company_name,
            "valid_until": v.valid_until.isoformat() if v.valid_until else None,
            "is_used": v.is_used,
            "used_at": v.used_at.isoformat() if v.used_at else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in vouchers
    ]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["router"]
