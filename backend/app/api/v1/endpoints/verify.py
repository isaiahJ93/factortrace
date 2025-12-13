# app/api/v1/endpoints/verify.py
"""
Report Verification Endpoint.

Provides public (no-auth) verification of signed compliance reports.
This is the endpoint QR codes point to for tamper-evidence verification.

See docs/features/verification-layer.md
"""
import logging
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.wizard import ComplianceWizardSession, WizardStatus
from app.services.crypto_service import (
    CryptoService,
    generate_verification_qr,
    get_crypto_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# SCHEMAS
# =============================================================================

class VerificationStatus(str, Enum):
    """Status of report verification."""
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    NOT_FOUND = "NOT_FOUND"
    NOT_SIGNED = "NOT_SIGNED"


class CompanyInfo(BaseModel):
    """Basic company info from the report."""
    name: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None


class EmissionsSummary(BaseModel):
    """High-level emissions summary (no detailed data)."""
    total_tco2e: Optional[float] = None
    scope1_tco2e: Optional[float] = None
    scope2_tco2e: Optional[float] = None
    scope3_tco2e: Optional[float] = None
    reporting_period: Optional[str] = None


class VerificationResponse(BaseModel):
    """Response for report verification request."""
    status: VerificationStatus
    report_id: str

    # Verification details
    hash_verified: bool = False
    signature_verified: bool = False
    signed_at: Optional[datetime] = None

    # Report metadata (public, non-sensitive)
    company: Optional[CompanyInfo] = None
    emissions_summary: Optional[EmissionsSummary] = None
    report_completed_at: Optional[datetime] = None

    # Verification metadata
    public_key_hex: Optional[str] = None
    verification_url: Optional[str] = None
    message: Optional[str] = None


class VerificationBadgeResponse(BaseModel):
    """Badge/status response for embedding."""
    status: VerificationStatus
    badge_text: str
    color: str  # green, red, yellow
    report_id: str
    signed_at: Optional[datetime] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _extract_company_info(session: ComplianceWizardSession) -> Optional[CompanyInfo]:
    """Extract company info from wizard session."""
    if not session.company_profile:
        return None

    profile = session.company_profile
    return CompanyInfo(
        name=profile.get("name") or profile.get("company_name"),
        country=profile.get("country") or profile.get("country_code"),
        industry=profile.get("industry_nace") or profile.get("industry"),
    )


def _extract_emissions_summary(session: ComplianceWizardSession) -> Optional[EmissionsSummary]:
    """Extract emissions summary from wizard session."""
    if not session.calculated_emissions:
        return None

    emissions = session.calculated_emissions
    return EmissionsSummary(
        total_tco2e=emissions.get("total_tco2e"),
        scope1_tco2e=emissions.get("scope1_tco2e"),
        scope2_tco2e=emissions.get("scope2_tco2e"),
        scope3_tco2e=emissions.get("scope3_tco2e"),
        reporting_period=emissions.get("reporting_period"),
    )


def _build_report_data_for_verification(session: ComplianceWizardSession) -> dict:
    """Build the report data dict used for hash verification."""
    return {
        "company_profile": session.company_profile,
        "activity_data": session.activity_data,
        "calculated_emissions": session.calculated_emissions,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
    }


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/{report_id}",
    response_model=VerificationResponse,
    summary="Verify a signed report",
    description="Public endpoint (no auth required) to verify report authenticity",
)
async def verify_report(
    report_id: str,
    db: Session = Depends(get_db),
) -> VerificationResponse:
    """
    Verify a signed compliance report.

    This is the endpoint that QR codes point to. It verifies:
    1. The report exists and is completed
    2. The content hash matches (report hasn't been tampered with)
    3. The signature is valid (report was signed by FactorTrace)

    Args:
        report_id: The wizard session ID (used as report ID)

    Returns:
        VerificationResponse with status and metadata
    """
    # Find the report/wizard session
    # Note: report_id is the wizard session ID
    try:
        session_id = int(report_id)
    except ValueError:
        return VerificationResponse(
            status=VerificationStatus.NOT_FOUND,
            report_id=report_id,
            message="Invalid report ID format",
        )

    session = db.query(ComplianceWizardSession).filter(
        ComplianceWizardSession.id == session_id
    ).first()

    if not session:
        logger.warning(f"Verification attempt for non-existent report: {report_id}")
        return VerificationResponse(
            status=VerificationStatus.NOT_FOUND,
            report_id=report_id,
            message="Report not found",
        )

    # Check if report is completed
    if session.status != WizardStatus.COMPLETED:
        return VerificationResponse(
            status=VerificationStatus.NOT_FOUND,
            report_id=report_id,
            message="Report is not yet completed",
        )

    # Check if report is signed
    if not session.report_hash or not session.signature:
        return VerificationResponse(
            status=VerificationStatus.NOT_SIGNED,
            report_id=report_id,
            hash_verified=False,
            signature_verified=False,
            company=_extract_company_info(session),
            emissions_summary=_extract_emissions_summary(session),
            report_completed_at=session.completed_at,
            message="Report exists but has not been digitally signed",
        )

    # Get crypto service
    crypto = get_crypto_service()

    # Build report data for verification
    report_data = _build_report_data_for_verification(session)

    # Verify the report
    try:
        is_valid = crypto.verify_report(
            report_id=str(session.id),
            report_data=report_data,
            content_hash=session.report_hash,
            signature=session.signature,
            signed_at=session.signed_at,
            tenant_id=session.tenant_id,
        )

        if is_valid:
            logger.info(f"Report {report_id} verified successfully")
            return VerificationResponse(
                status=VerificationStatus.VERIFIED,
                report_id=report_id,
                hash_verified=True,
                signature_verified=True,
                signed_at=session.signed_at,
                company=_extract_company_info(session),
                emissions_summary=_extract_emissions_summary(session),
                report_completed_at=session.completed_at,
                public_key_hex=crypto.get_public_key_hex(),
                verification_url=session.verification_url,
                message="Report is authentic and has not been modified",
            )
        else:
            logger.warning(f"Report {report_id} failed verification")
            return VerificationResponse(
                status=VerificationStatus.FAILED,
                report_id=report_id,
                hash_verified=False,
                signature_verified=False,
                signed_at=session.signed_at,
                company=_extract_company_info(session),
                report_completed_at=session.completed_at,
                message="Report verification failed - content may have been modified",
            )

    except ValueError as e:
        logger.error(f"Verification error for report {report_id}: {e}")
        return VerificationResponse(
            status=VerificationStatus.FAILED,
            report_id=report_id,
            hash_verified=False,
            signature_verified=False,
            message=f"Verification error: {str(e)}",
        )


@router.get(
    "/{report_id}/badge",
    response_model=VerificationBadgeResponse,
    summary="Get verification badge",
    description="Get a simple badge/status for embedding in documents",
)
async def get_verification_badge(
    report_id: str,
    db: Session = Depends(get_db),
) -> VerificationBadgeResponse:
    """
    Get a simple verification badge for embedding.

    Returns a simplified status suitable for displaying in documents
    or external systems.
    """
    # Use the main verify endpoint logic
    result = await verify_report(report_id, db)

    # Map status to badge
    if result.status == VerificationStatus.VERIFIED:
        return VerificationBadgeResponse(
            status=result.status,
            badge_text="VERIFIED",
            color="green",
            report_id=report_id,
            signed_at=result.signed_at,
        )
    elif result.status == VerificationStatus.NOT_SIGNED:
        return VerificationBadgeResponse(
            status=result.status,
            badge_text="NOT SIGNED",
            color="yellow",
            report_id=report_id,
        )
    elif result.status == VerificationStatus.NOT_FOUND:
        return VerificationBadgeResponse(
            status=result.status,
            badge_text="NOT FOUND",
            color="red",
            report_id=report_id,
        )
    else:
        return VerificationBadgeResponse(
            status=result.status,
            badge_text="FAILED",
            color="red",
            report_id=report_id,
            signed_at=result.signed_at,
        )


@router.get(
    "/{report_id}/qr",
    summary="Get verification QR code",
    description="Get QR code image for the verification URL",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "QR code PNG image",
        }
    },
)
async def get_verification_qr(
    report_id: str,
    size: int = 200,
    db: Session = Depends(get_db),
) -> Response:
    """
    Generate QR code for report verification URL.

    Args:
        report_id: Report/session ID
        size: QR code size in pixels (default 200, max 500)

    Returns:
        PNG image of QR code
    """
    # Validate size
    if size < 50:
        size = 50
    elif size > 500:
        size = 500

    # Validate report exists
    try:
        session_id = int(report_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid report ID",
        )

    session = db.query(ComplianceWizardSession).filter(
        ComplianceWizardSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # Generate QR code
    try:
        qr_bytes = generate_verification_qr(report_id)
        return Response(
            content=qr_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
            }
        )
    except Exception as e:
        logger.error(f"Failed to generate QR code for report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate QR code",
        )


@router.get(
    "/public-key",
    summary="Get public key for offline verification",
    description="Get the Ed25519 public key for offline signature verification",
)
async def get_public_key() -> dict:
    """
    Get the public key for offline verification.

    Third parties can use this public key to verify signatures
    without calling the API.

    Returns:
        Public key in hex format and usage instructions
    """
    crypto = get_crypto_service()
    public_key = crypto.get_public_key_hex()

    if not public_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Signing service not configured",
        )

    return {
        "algorithm": "Ed25519",
        "public_key_hex": public_key,
        "usage": "Verify signatures using Ed25519 with the hex-encoded public key",
        "signature_format": "hex-encoded 64-byte Ed25519 signature",
        "signed_payload_format": "{content_hash}|{report_id}|{signed_at_iso}|{tenant_id}",
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["router"]
