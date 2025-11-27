# app/api/v1/endpoints/voucher_system.py
"""
API endpoints for voucher redemption and session management
Integrates with Stripe webhooks and Supabase auth
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import stripe
import hashlib
import hmac
import json

from app.db.session import get_db
from app.services.voucher_service import (
    VoucherService, 
    get_voucher_service,
    VoucherRedemptionRequest,
    VoucherRedemptionResponse,
    SessionValidationResponse
)
from app.core.config import settings

router = APIRouter(prefix="/api/v1/voucher", tags=["voucher"])
security = HTTPBearer()

# ============================================================================
# MIDDLEWARE FOR SESSION VALIDATION
# ============================================================================

class VoucherSessionMiddleware:
    """
    Middleware to validate voucher sessions and enforce lockdown
    """
    
    def __init__(self, require_calculator_access: bool = False, 
                 require_export_access: bool = False):
        self.require_calculator_access = require_calculator_access
        self.require_export_access = require_export_access
    
    async def __call__(
        self,
        request: Request,
        db: Session = Depends(get_db),
        voucher_service: VoucherService = Depends(get_voucher_service),
        authorization: Optional[str] = Header(None)
    ) -> Dict[str, Any]:
        """
        Validate session token and check permissions
        """
        # Extract session token from header
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        session_token = authorization.replace("Bearer ", "")
        
        # Validate session
        session_info = await voucher_service.validate_session(db, session_token)
        
        if not session_info.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
        
        # Check calculator access if required
        if self.require_calculator_access and not session_info.calculator_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Calculator access has been disabled after report generation"
            )
        
        # Check export access if required
        if self.require_export_access and not session_info.export_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Export functionality has been disabled after report generation"
            )
        
        return {
            "session_token": session_token,
            "voucher_id": session_info.voucher_id,
            "report_generated": session_info.report_generated,
            "calculator_access": session_info.calculator_access,
            "export_access": session_info.export_access
        }

# Dependency injections for different access levels
require_valid_session = VoucherSessionMiddleware()
require_calculator_access = VoucherSessionMiddleware(require_calculator_access=True)
require_export_access = VoucherSessionMiddleware(require_export_access=True)

# ============================================================================
# VOUCHER REDEMPTION ENDPOINTS
# ============================================================================

@router.post("/redeem", response_model=VoucherRedemptionResponse)
async def redeem_voucher(
    request: Request,
    redemption_request: VoucherRedemptionRequest,
    db: Session = Depends(get_db),
    voucher_service: VoucherService = Depends(get_voucher_service)
):
    """
    Redeem a voucher code and create a session
    
    This endpoint:
    1. Validates the Supabase auth token
    2. Checks voucher validity
    3. Performs atomic redemption with race condition prevention
    4. Returns session token for calculator access
    """
    # Get client IP and user agent
    client_ip = request.client.host
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    # Perform redemption
    result = await voucher_service.redeem_voucher(
        db=db,
        code=redemption_request.code,
        supabase_token=redemption_request.supabase_token,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )
    
    return result


@router.get("/validate-session", response_model=SessionValidationResponse)
async def validate_session(
    session_info: Dict = Depends(require_valid_session)
):
    """
    Validate current session and return permissions
    """
    return SessionValidationResponse(
        valid=True,
        voucher_id=session_info["voucher_id"],
        report_generated=session_info["report_generated"],
        calculator_access=session_info["calculator_access"],
        export_access=session_info["export_access"]
    )


# ============================================================================
# STRIPE WEBHOOK ENDPOINT
# ============================================================================

@router.post("/stripe-webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    voucher_service: VoucherService = Depends(get_voucher_service)
):
    """
    Handle Stripe webhook events for voucher creation
    Creates voucher after successful payment
    """
    # Get raw body for signature verification
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    # Handle checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Create voucher
        result = await voucher_service.create_voucher_from_stripe(
            db=db,
            stripe_session_id=session["id"],
            stripe_payment_intent_id=session["payment_intent"],
            customer_email=session["customer_details"]["email"],
            amount=session["amount_total"],
            currency=session["currency"].upper()
        )
        
        # TODO: Send voucher code via email to customer
        # await send_voucher_email(
        #     email=session["customer_details"]["email"],
        #     voucher_code=result["voucher_code"]
        # )
        
        return {"success": True, "voucher_created": True}
    
    # Handle other events as needed
    return {"success": True}


# ============================================================================
# PROTECTED CALCULATOR ENDPOINTS
# ============================================================================

@router.post("/calculator/calculate")
async def calculate_emissions(
    request: Request,
    session_info: Dict = Depends(require_calculator_access),
    db: Session = Depends(get_db)
):
    """
    Protected endpoint for emissions calculation
    Requires valid session with calculator access
    """
    # Your existing calculator logic here
    # Forward to the actual calculator endpoint
    
    # Get request body
    body = await request.json()
    
    # Add session info to the request
    body["voucher_id"] = session_info["voucher_id"]
    body["session_token"] = session_info["session_token"]
    
    # Forward to actual calculator
    # This would call your existing calculator service
    
    return {
        "success": True,
        "message": "Calculation performed",
        "voucher_id": session_info["voucher_id"]
    }


@router.post("/calculator/generate-report")
async def generate_report(
    request: Request,
    session_info: Dict = Depends(require_export_access),
    db: Session = Depends(get_db),
    voucher_service: VoucherService = Depends(get_voucher_service)
):
    """
    Generate final report and lock session
    This is the ONE-TIME operation that locks everything down
    """
    # Check if report already generated
    if session_info["report_generated"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report has already been generated for this voucher"
        )
    
    # Get report data from request
    report_data = await request.json()
    
    # TODO: Forward to your actual report generation endpoint
    # generated_report = await generate_actual_report(report_data)
    
    # Lock the session after report generation
    locked = await voucher_service.lock_session_after_report(
        db=db,
        session_token=session_info["session_token"],
        report_data=report_data
    )
    
    if not locked:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lock session after report generation"
        )
    
    return {
        "success": True,
        "message": "Report generated successfully",
        "report_url": "/api/v1/reports/download/" + session_info["voucher_id"],
        "access_locked": True
    }


# ============================================================================
# INTEGRATION WITH EXISTING ENDPOINTS
# ============================================================================

from app.api.v1.endpoints.esrs_e1_full_backup import router as esrs_router

@router.post("/export/esrs-e1-protected")
async def protected_esrs_export(
    request: Request,
    session_info: Dict = Depends(require_export_access),
    db: Session = Depends(get_db),
    voucher_service: VoucherService = Depends(get_voucher_service)
):
    """
    Protected wrapper for ESRS E1 export
    Integrates with your existing endpoint
    """
    # Check if report already generated
    if session_info["report_generated"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Export has already been used for this voucher"
        )
    
    # Get request body
    body = await request.json()
    
    # Forward to existing ESRS endpoint
    # You would import and call your existing function here
    # from app.api.v1.endpoints.esrs_e1_full_backup import generate_esrs_report
    # report_result = await generate_esrs_report(body)
    
    # Lock session after successful export
    await voucher_service.lock_session_after_report(
        db=db,
        session_token=session_info["session_token"],
        report_data={
            "type": "ESRS_E1",
            "timestamp": datetime.utcnow().isoformat(),
            "data": body
        }
    )
    
    return {
        "success": True,
        "message": "ESRS report generated",
        "access_locked": True
    }


# ============================================================================
# ADMIN ENDPOINTS (Optional)
# ============================================================================

@router.get("/admin/voucher/{voucher_code}")
async def get_voucher_status(
    voucher_code: str,
    db: Session = Depends(get_db),
    # Add your admin authentication here
    # admin_user = Depends(require_admin)
):
    """
    Admin endpoint to check voucher status
    """
    from app.models.voucher import Voucher
    
    voucher = db.query(Voucher).filter(
        Voucher.code == voucher_code
    ).first()
    
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found"
        )
    
    return {
        "code": voucher.code,
        "status": voucher.status.value,
        "created_at": voucher.created_at.isoformat(),
        "redeemed_at": voucher.redeemed_at.isoformat() if voucher.redeemed_at else None,
        "expires_at": voucher.expires_at.isoformat()
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
    voucher_service: VoucherService = Depends(get_voucher_service)
):
    """
    Health check for voucher system
    """
    try:
        # Check database
        db.execute("SELECT 1")
        
        # Check Redis if available
        redis_healthy = False
        if voucher_service.redis_client:
            await voucher_service.redis_client.ping()
            redis_healthy = True
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected" if redis_healthy else "not configured",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )