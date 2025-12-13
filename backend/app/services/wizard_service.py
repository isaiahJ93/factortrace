# app/services/wizard_service.py
"""
Compliance Wizard Service.

Provides business logic for the self-serve compliance wizard:
- Session management (create, update, get)
- Emissions calculation
- Report generation trigger

This is the "€500 magic moment" engine.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from sqlalchemy.orm import Session

from app.models.wizard import (
    ComplianceWizardSession,
    IndustryTemplate,
    WizardStatus,
)
from app.models.voucher import Voucher, VoucherStatus
from app.schemas.wizard import (
    CompanyProfile,
    ActivityData,
    CalculatedEmissions,
    EmissionBreakdownItem,
)
from app.services.emission_factors import get_factor
from app.services.crypto_service import get_crypto_service

logger = logging.getLogger(__name__)


# =============================================================================
# ACTIVITY TO EMISSION FACTOR MAPPING
# =============================================================================

# Maps activity field names to emission factor lookup parameters
# Format: (scope, category, activity_type, unit)
ACTIVITY_FACTOR_MAP: Dict[str, Tuple[int, str, str, str]] = {
    # Scope 1: Direct emissions
    "natural_gas_m3": (1, "fuels", "Natural Gas", "m3"),
    "diesel_l": (1, "fuels", "Diesel", "litre"),
    "petrol_l": (1, "fuels", "Petrol", "litre"),
    "lpg_kg": (1, "fuels", "LPG", "kg"),
    "heating_oil_l": (1, "fuels", "Heating Oil", "litre"),
    "company_vehicles_km": (1, "transport", "Company Vehicles - Average", "km"),

    # Scope 2: Indirect emissions
    "electricity_kwh": (2, "electricity", "Electricity - Grid Average", "kWh"),
    "renewable_electricity_kwh": (2, "electricity", "Electricity - Renewable", "kWh"),
    "district_heating_kwh": (2, "heat", "District Heating", "kWh"),
    "district_cooling_kwh": (2, "cooling", "District Cooling", "kWh"),

    # Scope 3: Value chain emissions
    "business_travel_km": (3, "business_travel", "Air Travel - Average", "km"),
    "business_travel_rail_km": (3, "business_travel", "Rail Travel", "km"),
    "employee_commute_km": (3, "employee_commuting", "Commuting - Average", "km"),
    "waste_kg": (3, "waste", "Waste - General", "kg"),
    "waste_recycled_kg": (3, "waste", "Waste - Recycled", "kg"),
    "water_m3": (3, "water", "Water Supply", "m3"),

    # Spend-based Scope 3 (EXIOBASE)
    "purchased_goods_eur": (3, "spend_based", "Purchased Goods & Services", "EUR"),
    "capital_goods_eur": (3, "spend_based", "Capital Goods", "EUR"),
    "upstream_transport_eur": (3, "spend_based", "Upstream Transportation", "EUR"),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_tenant_session(
    db: Session,
    session_id: int,
    tenant_id: str,
) -> Optional[ComplianceWizardSession]:
    """Get wizard session with tenant isolation."""
    return (
        db.query(ComplianceWizardSession)
        .filter(
            ComplianceWizardSession.id == session_id,
            ComplianceWizardSession.tenant_id == tenant_id,
        )
        .first()
    )


def _validate_voucher(
    db: Session,
    voucher_code: str,
    tenant_id: str,
) -> Optional[Voucher]:
    """Validate and return voucher if valid for use."""
    voucher = (
        db.query(Voucher)
        .filter(
            Voucher.code == voucher_code,
            Voucher.tenant_id == tenant_id,
            Voucher.status == VoucherStatus.VALID,
            Voucher.is_used == False,
        )
        .first()
    )

    if voucher and voucher.valid_until < datetime.utcnow():
        return None  # Expired

    return voucher


def _mark_voucher_used(voucher: Voucher) -> None:
    """Mark voucher as used."""
    voucher.status = VoucherStatus.USED
    voucher.is_used = True
    voucher.used_at = datetime.utcnow()


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

def create_wizard_session(
    db: Session,
    *,
    tenant_id: str,
    voucher_code: Optional[str] = None,
    template_id: Optional[str] = None,
    user_id: Optional[int] = None,
) -> ComplianceWizardSession:
    """
    Create a new wizard session.

    Args:
        db: Database session
        tenant_id: Tenant ID (from auth)
        voucher_code: Optional voucher code to redeem
        template_id: Optional industry template to pre-populate
        user_id: Optional user ID who created the session

    Returns:
        Created wizard session
    """
    voucher_id = None

    # Validate and redeem voucher if provided
    if voucher_code:
        voucher = _validate_voucher(db, voucher_code, tenant_id)
        if not voucher:
            raise ValueError(f"Invalid or expired voucher code: {voucher_code}")
        voucher_id = voucher.id
        _mark_voucher_used(voucher)

    # Load template defaults if provided
    company_profile = None
    activity_data = None
    if template_id:
        template = db.query(IndustryTemplate).filter(
            IndustryTemplate.id == template_id,
            IndustryTemplate.is_active == 1,
        ).first()
        if template and template.smart_defaults:
            activity_data = template.smart_defaults

    session = ComplianceWizardSession(
        tenant_id=tenant_id,
        voucher_id=voucher_id,
        template_id=template_id,
        status=WizardStatus.DRAFT,
        current_step="company_profile",
        company_profile=company_profile,
        activity_data=activity_data,
        created_by_user_id=user_id,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    logger.info(f"Created wizard session {session.id} for tenant {tenant_id}")
    return session


def get_wizard_session(
    db: Session,
    *,
    session_id: int,
    tenant_id: str,
) -> Optional[ComplianceWizardSession]:
    """Get wizard session by ID with tenant isolation."""
    return _get_tenant_session(db, session_id, tenant_id)


def list_wizard_sessions(
    db: Session,
    *,
    tenant_id: str,
    status: Optional[WizardStatus] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[ComplianceWizardSession]:
    """List wizard sessions for a tenant."""
    query = db.query(ComplianceWizardSession).filter(
        ComplianceWizardSession.tenant_id == tenant_id,
    )

    if status:
        query = query.filter(ComplianceWizardSession.status == status)

    return (
        query
        .order_by(ComplianceWizardSession.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_wizard_session(
    db: Session,
    *,
    session_id: int,
    tenant_id: str,
    current_step: Optional[str] = None,
    company_profile: Optional[CompanyProfile] = None,
    activity_data: Optional[ActivityData] = None,
    notes: Optional[str] = None,
) -> Optional[ComplianceWizardSession]:
    """
    Update wizard session data.

    Updates company profile and/or activity data, tracks current step.
    """
    session = _get_tenant_session(db, session_id, tenant_id)
    if not session:
        return None

    # Update status to in_progress if still draft
    if session.status == WizardStatus.DRAFT:
        session.status = WizardStatus.IN_PROGRESS

    # Update fields
    if current_step:
        session.current_step = current_step

    if company_profile:
        session.company_profile = company_profile.model_dump()

    if activity_data:
        session.activity_data = activity_data.model_dump(exclude_none=True)

    if notes is not None:
        session.notes = notes

    db.commit()
    db.refresh(session)

    return session


def abandon_wizard_session(
    db: Session,
    *,
    session_id: int,
    tenant_id: str,
) -> bool:
    """Mark a wizard session as abandoned."""
    session = _get_tenant_session(db, session_id, tenant_id)
    if not session:
        return False

    session.status = WizardStatus.ABANDONED
    db.commit()

    return True


# =============================================================================
# EMISSIONS CALCULATION
# =============================================================================

def calculate_emissions(
    db: Session,
    *,
    session_id: int,
    tenant_id: str,
    recalculate: bool = False,
) -> Tuple[Optional[CalculatedEmissions], List[str], List[str]]:
    """
    Calculate emissions for a wizard session.

    Args:
        db: Database session
        session_id: Wizard session ID
        tenant_id: Tenant ID
        recalculate: If True, recalculate even if already done

    Returns:
        Tuple of (CalculatedEmissions or None, errors list, warnings list)
    """
    session = _get_tenant_session(db, session_id, tenant_id)
    if not session:
        return None, ["Session not found"], []

    if session.calculated_emissions and not recalculate:
        # Return cached result
        return CalculatedEmissions(**session.calculated_emissions), [], []

    if not session.activity_data:
        return None, ["No activity data provided"], []

    # Get country from company profile
    country_code = "GLOBAL"
    reporting_year = 2024
    if session.company_profile:
        country_code = session.company_profile.get("country", "GLOBAL")
        reporting_year = session.company_profile.get("reporting_year", 2024)

    # Calculate emissions for each activity
    breakdown: List[EmissionBreakdownItem] = []
    errors: List[str] = []
    warnings: List[str] = []

    scope1_total = 0.0
    scope2_total = 0.0
    scope3_total = 0.0

    activity_data = session.activity_data

    for field_name, (scope, category, activity_type, unit) in ACTIVITY_FACTOR_MAP.items():
        value = activity_data.get(field_name)
        if value is None or value == 0:
            continue

        # Get emission factor
        factor = get_factor(
            db,
            scope=scope,
            category=category,
            activity_type=activity_type,
            country_code=country_code,
            year=reporting_year,
        )

        if factor is None:
            # Try GLOBAL fallback
            factor = get_factor(
                db,
                scope=scope,
                category=category,
                activity_type=activity_type,
                country_code="GLOBAL",
                year=reporting_year,
            )

        if factor is None:
            warnings.append(
                f"No emission factor found for {field_name} ({category}/{activity_type})"
            )
            continue

        # Calculate emissions
        emissions_kgco2e = float(value) * factor
        emissions_tco2e = emissions_kgco2e / 1000.0

        # Determine dataset (default for now)
        dataset = "DEFRA_2024" if scope <= 2 else "EXIOBASE_2020"

        breakdown.append(EmissionBreakdownItem(
            category=field_name,
            scope=scope,
            activity_value=float(value),
            activity_unit=unit,
            emission_factor=factor,
            factor_unit=f"kgCO2e/{unit}",
            factor_dataset=dataset,
            emissions_kgco2e=emissions_kgco2e,
            emissions_tco2e=emissions_tco2e,
        ))

        # Sum by scope
        if scope == 1:
            scope1_total += emissions_tco2e
        elif scope == 2:
            scope2_total += emissions_tco2e
        else:
            scope3_total += emissions_tco2e

    # Create result
    result = CalculatedEmissions(
        scope1_tco2e=round(scope1_total, 4),
        scope2_tco2e=round(scope2_total, 4),
        scope3_tco2e=round(scope3_total, 4),
        total_tco2e=round(scope1_total + scope2_total + scope3_total, 4),
        breakdown=breakdown,
        methodology_notes=(
            f"Calculated using emission factors for {country_code} "
            f"(year {reporting_year}). DEFRA 2024 for Scope 1/2, "
            f"EXIOBASE 2020 for spend-based Scope 3."
        ),
        calculated_at=datetime.utcnow(),
    )

    # Store in session
    session.calculated_emissions = result.model_dump(mode="json")
    db.commit()

    return result, errors, warnings


def complete_wizard_session(
    db: Session,
    *,
    session_id: int,
    tenant_id: str,
    report_id: Optional[int] = None,
) -> Optional[ComplianceWizardSession]:
    """
    Mark wizard session as completed and sign the report.

    Called after report generation succeeds.
    Signs the report with Ed25519 for tamper-evidence.
    """
    session = _get_tenant_session(db, session_id, tenant_id)
    if not session:
        return None

    session.status = WizardStatus.COMPLETED
    session.completed_at = datetime.utcnow()
    if report_id:
        session.report_id = report_id

    # Sign the report (Phase 1 + 2 verification layer)
    _sign_wizard_report(session)

    db.commit()
    db.refresh(session)

    logger.info(f"Completed wizard session {session_id} with report {report_id}")
    return session


def _sign_wizard_report(session: ComplianceWizardSession) -> None:
    """
    Sign the wizard session report with Ed25519.

    Sets report_hash, signature, signed_at, and verification_url on the session.
    Silently skips signing if crypto service is not configured.
    """
    try:
        crypto = get_crypto_service()

        # Check if signing is configured
        if not crypto.is_configured():
            logger.warning(
                f"Signing skipped for session {session.id}: crypto service not configured"
            )
            return

        # Build report data for signing
        report_data = {
            "company_profile": session.company_profile,
            "activity_data": session.activity_data,
            "calculated_emissions": session.calculated_emissions,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }

        # Sign the report
        signed = crypto.sign_report(
            report_id=str(session.id),
            report_data=report_data,
            tenant_id=session.tenant_id,
        )

        # Store signing results
        session.report_hash = signed.content_hash
        session.signature = signed.signature
        session.signed_at = signed.signed_at
        session.verification_url = signed.verification_url

        logger.info(f"Signed wizard session {session.id} report at {signed.signed_at}")

    except Exception as e:
        # Don't fail completion if signing fails - log and continue
        logger.error(f"Failed to sign report for session {session.id}: {e}")


# =============================================================================
# INDUSTRY TEMPLATES
# =============================================================================

def get_industry_templates(
    db: Session,
    *,
    company_size: Optional[str] = None,
    nace_code: Optional[str] = None,
) -> List[IndustryTemplate]:
    """
    List available industry templates.

    Args:
        db: Database session
        company_size: Filter by company size (micro, small, medium, large)
        nace_code: Filter by NACE code prefix

    Returns:
        List of matching templates
    """
    query = db.query(IndustryTemplate).filter(IndustryTemplate.is_active == 1)

    if company_size:
        query = query.filter(IndustryTemplate.company_size == company_size)

    templates = query.order_by(IndustryTemplate.display_order).all()

    # Filter by NACE code if provided
    if nace_code:
        nace_prefix = nace_code.upper()[:2]  # e.g., "C10" -> "C1"
        templates = [
            t for t in templates
            if any(n.startswith(nace_prefix) for n in (t.nace_codes or []))
        ]

    return templates


def get_template_by_id(
    db: Session,
    template_id: str,
) -> Optional[IndustryTemplate]:
    """Get a specific industry template by ID."""
    return (
        db.query(IndustryTemplate)
        .filter(
            IndustryTemplate.id == template_id,
            IndustryTemplate.is_active == 1,
        )
        .first()
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Session management
    "create_wizard_session",
    "get_wizard_session",
    "list_wizard_sessions",
    "update_wizard_session",
    "abandon_wizard_session",
    # Calculation
    "calculate_emissions",
    "complete_wizard_session",
    # Templates
    "get_industry_templates",
    "get_template_by_id",
]
