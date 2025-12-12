# app/api/v1/endpoints/wizard.py
"""
Self-Serve Compliance Wizard API Endpoints.

Provides endpoints for the "€500 magic moment" - guiding Tier 2 suppliers
from voucher redemption to a complete compliance report in ~10 minutes.

Security:
- All session data filtered by tenant_id from JWT
- Voucher validation on session creation
- Cross-tenant access returns 404 (not 403) to prevent enumeration

Flow:
1. POST /sessions - Create session (optionally with voucher)
2. PUT /sessions/{id}/company-profile - Submit company info
3. PUT /sessions/{id}/activity-data - Submit activity data
4. POST /sessions/{id}/calculate - Calculate emissions
5. POST /sessions/{id}/generate-report - Generate compliance report
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user
from app.schemas.auth_schemas import CurrentUser
from app.models.wizard import WizardStatus

# Wizard Schemas
from app.schemas.wizard import (
    # Session schemas
    WizardSessionCreate,
    WizardSessionUpdate,
    WizardSessionResponse,
    WizardSessionSummary,
    # Data schemas
    CompanyProfile,
    ActivityData,
    CalculatedEmissions,
    # Template schemas
    IndustryTemplateResponse,
    # Request/Response schemas
    SmartDefaultsRequest,
    SmartDefaultsResponse,
    CalculateEmissionsRequest,
    CalculateEmissionsResponse,
    GenerateReportRequest,
    GenerateReportResponse,
)

# Wizard Service
from app.services import wizard_service

router = APIRouter(tags=["Wizard"])


# =============================================================================
# WIZARD SESSIONS
# =============================================================================

@router.post(
    "/sessions",
    response_model=WizardSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Wizard Session",
    description="Start a new compliance wizard session. Optionally redeem a voucher.",
)
async def create_session(
    request: WizardSessionCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create a new wizard session.

    If voucher_code is provided, the voucher will be validated and redeemed.
    If template_id is provided, smart defaults will be pre-populated.
    """
    try:
        session = wizard_service.create_wizard_session(
            db,
            tenant_id=current_user.tenant_id,
            voucher_code=request.voucher_code,
            template_id=request.template_id,
            user_id=int(current_user.id) if current_user.id.isdigit() else None,
        )
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/sessions",
    response_model=List[WizardSessionSummary],
    summary="List Wizard Sessions",
    description="List all wizard sessions for the current tenant.",
)
async def list_sessions(
    status_filter: Optional[WizardStatus] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List wizard sessions for the current tenant."""
    sessions = wizard_service.list_wizard_sessions(
        db,
        tenant_id=current_user.tenant_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    # Convert to summary format
    summaries = []
    for s in sessions:
        company_name = None
        total_tco2e = None

        if s.company_profile:
            company_name = s.company_profile.get("name")
        if s.calculated_emissions:
            total_tco2e = s.calculated_emissions.get("total_tco2e")

        summaries.append(WizardSessionSummary(
            id=s.id,
            tenant_id=s.tenant_id,
            status=s.status,
            current_step=s.current_step,
            company_name=company_name,
            total_tco2e=total_tco2e,
            template_id=s.template_id,
            created_at=s.created_at,
            completed_at=s.completed_at,
        ))

    return summaries


@router.get(
    "/sessions/{session_id}",
    response_model=WizardSessionResponse,
    summary="Get Wizard Session",
    description="Get details of a specific wizard session.",
)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a wizard session by ID."""
    session = wizard_service.get_wizard_session(
        db,
        session_id=session_id,
        tenant_id=current_user.tenant_id,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return session


@router.put(
    "/sessions/{session_id}/company-profile",
    response_model=WizardSessionResponse,
    summary="Update Company Profile",
    description="Submit or update the company profile (Step 1).",
)
async def update_company_profile(
    session_id: int,
    company_profile: CompanyProfile,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update company profile for a wizard session."""
    session = wizard_service.update_wizard_session(
        db,
        session_id=session_id,
        tenant_id=current_user.tenant_id,
        current_step="activity_data",
        company_profile=company_profile,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return session


@router.put(
    "/sessions/{session_id}/activity-data",
    response_model=WizardSessionResponse,
    summary="Update Activity Data",
    description="Submit or update activity data (Step 2).",
)
async def update_activity_data(
    session_id: int,
    activity_data: ActivityData,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update activity data for a wizard session."""
    session = wizard_service.update_wizard_session(
        db,
        session_id=session_id,
        tenant_id=current_user.tenant_id,
        current_step="calculate",
        activity_data=activity_data,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return session


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Abandon Session",
    description="Mark a wizard session as abandoned.",
)
async def abandon_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Abandon a wizard session."""
    success = wizard_service.abandon_wizard_session(
        db,
        session_id=session_id,
        tenant_id=current_user.tenant_id,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return None


# =============================================================================
# EMISSIONS CALCULATION
# =============================================================================

@router.post(
    "/sessions/{session_id}/calculate",
    response_model=CalculateEmissionsResponse,
    summary="Calculate Emissions",
    description="Calculate emissions based on submitted activity data.",
)
async def calculate_emissions(
    session_id: int,
    recalculate: bool = Query(False, description="Force recalculation"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Calculate emissions for a wizard session.

    Uses the company country to select appropriate emission factors.
    DEFRA 2024 for Scope 1/2, EXIOBASE 2020 for spend-based Scope 3.
    """
    emissions, errors, warnings = wizard_service.calculate_emissions(
        db,
        session_id=session_id,
        tenant_id=current_user.tenant_id,
        recalculate=recalculate,
    )

    if errors:
        return CalculateEmissionsResponse(
            session_id=session_id,
            status="error",
            emissions=None,
            errors=errors,
            warnings=warnings,
        )

    return CalculateEmissionsResponse(
        session_id=session_id,
        status="success",
        emissions=emissions,
        errors=[],
        warnings=warnings,
    )


# =============================================================================
# REPORT GENERATION
# =============================================================================

@router.post(
    "/sessions/{session_id}/generate-report",
    response_model=GenerateReportResponse,
    summary="Generate Report",
    description="Generate a compliance report from the wizard session data.",
)
async def generate_report(
    session_id: int,
    request: GenerateReportRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate a compliance report from wizard session.

    This marks the session as completed and creates a formal report
    that can be downloaded in the requested format.
    """
    # First verify session exists and has calculated emissions
    session = wizard_service.get_wizard_session(
        db,
        session_id=session_id,
        tenant_id=current_user.tenant_id,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if not session.calculated_emissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Emissions must be calculated before generating report"
        )

    # TODO: Integrate with report generation service
    # For now, mark session as completed and return placeholder
    completed_session = wizard_service.complete_wizard_session(
        db,
        session_id=session_id,
        tenant_id=current_user.tenant_id,
        report_id=None,  # Will be set when report service is integrated
    )

    return GenerateReportResponse(
        session_id=session_id,
        report_id=completed_session.report_id if completed_session else None,
        format=request.format,
        status="success",
        file_url=None,  # Will be set when report service is integrated
        generated_at=datetime.utcnow(),
        errors=[],
    )


# =============================================================================
# INDUSTRY TEMPLATES
# =============================================================================

@router.get(
    "/templates",
    response_model=List[IndustryTemplateResponse],
    summary="List Industry Templates",
    description="Get available industry templates for the wizard.",
)
async def list_templates(
    company_size: Optional[str] = Query(None, pattern="^(micro|small|medium|large)$"),
    nace_code: Optional[str] = Query(None, max_length=10),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    List available industry templates.

    Templates provide smart defaults for common supplier types
    based on industry (NACE code) and company size.
    """
    templates = wizard_service.get_industry_templates(
        db,
        company_size=company_size,
        nace_code=nace_code,
    )
    return templates


@router.get(
    "/templates/{template_id}",
    response_model=IndustryTemplateResponse,
    summary="Get Industry Template",
    description="Get details of a specific industry template.",
)
async def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific industry template."""
    template = wizard_service.get_template_by_id(db, template_id)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return template


# =============================================================================
# SMART DEFAULTS
# =============================================================================

@router.post(
    "/smart-defaults",
    response_model=SmartDefaultsResponse,
    summary="Get Smart Defaults",
    description="Calculate smart defaults based on company profile.",
)
async def get_smart_defaults(
    request: SmartDefaultsRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Calculate smart defaults for activity data.

    Uses country, industry, and company size to estimate typical
    energy consumption and other activity data.
    """
    # Default methodology message
    methodology = (
        f"Defaults calculated for {request.country} based on "
        f"industry benchmarks and company size."
    )

    # Default recommended datasets
    recommended_datasets = {
        "scope1": "DEFRA_2024",
        "scope2": "DEFRA_2024",
        "scope3": "EXIOBASE_2020",
    }

    # Calculate defaults based on employee count
    defaults = {}
    confidence = "low"

    if request.employees:
        # Simple per-employee estimates (can be refined with real benchmarks)
        defaults = {
            "electricity_kwh": request.employees * 2500,  # ~2,500 kWh/employee/year
            "natural_gas_m3": request.employees * 50,  # ~50 m3/employee/year
            "business_travel_km": request.employees * 5000,  # ~5,000 km/employee/year
            "employee_commute_km": request.employees * 8000,  # ~8,000 km/employee/year
        }
        confidence = "medium"

        if request.industry_nace:
            methodology += f" Industry: {request.industry_nace}."
            confidence = "medium"

    elif request.annual_revenue_eur:
        # Revenue-based estimates for spend-based Scope 3
        defaults = {
            "purchased_goods_eur": request.annual_revenue_eur * 0.5,
            "capital_goods_eur": request.annual_revenue_eur * 0.05,
            "upstream_transport_eur": request.annual_revenue_eur * 0.03,
        }
        confidence = "low"

    # If template provided, use its defaults
    if request.template_id:
        template = wizard_service.get_template_by_id(db, request.template_id)
        if template and template.smart_defaults:
            defaults.update(template.smart_defaults)
            if template.recommended_datasets:
                recommended_datasets.update(template.recommended_datasets)
            confidence = "high"
            methodology = f"Defaults from template: {template.name}"

    return SmartDefaultsResponse(
        defaults=defaults,
        recommended_datasets=recommended_datasets,
        methodology=methodology,
        confidence=confidence,
    )
