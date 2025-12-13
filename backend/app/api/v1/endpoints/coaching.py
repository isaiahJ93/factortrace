# app/api/v1/endpoints/coaching.py
"""
Coaching Layer API Endpoints.

Provides supplier readiness assessment and improvement tracking.

Ethics Charter Compliance:
- NO numerical scores exposed (bands only)
- EVERY response includes improvement_actions[]
- Export endpoints required (GDPR/Charter Section 1)
- No blacklist or punitive features

See docs/features/coaching-layer.md for specification.
See docs/product/ethics-incentives.md for binding constraints.
"""
import io
import logging
from datetime import datetime
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.coaching import (
    CoachingAcknowledgment,
    ActionStatus,
    SupplierReadiness,
)
from app.schemas.coaching import (
    SupplierReadinessResponse,
    CoachingPassport,
    ImprovementAction,
    ActionStatusUpdate,
    ActionStatusResponse,
    ImprovementActionListResponse,
    CoachingExportRequest,
)
from app.services.coaching_engine import get_coaching_engine, SUPPORTED_REGIMES

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# ASSESSMENT ENDPOINTS
# =============================================================================

@router.get(
    "/{regime}/assess",
    response_model=SupplierReadinessResponse,
    summary="Assess supplier readiness for a regime",
    description="""
    Triggers a new readiness assessment for the authenticated supplier.

    Returns maturity bands for each dimension (not numerical scores),
    along with prioritized improvement actions.

    **Ethics Compliance:**
    - Returns bands, not scores (per Ethics Charter Section 2)
    - Always includes improvement_actions (minimum 1)
    - Rationale explains WHY each band was assigned
    """,
)
async def assess_readiness(
    regime: str,
    recalculate: bool = Query(False, description="Force recalculation even if recent assessment exists"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perform readiness assessment for a regime."""
    if regime not in SUPPORTED_REGIMES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported regime: {regime}. Supported: {SUPPORTED_REGIMES}"
        )

    engine = get_coaching_engine()

    # Check for recent assessment if not forcing recalculation
    if not recalculate:
        existing = (
            db.query(SupplierReadiness)
            .filter(
                SupplierReadiness.tenant_id == current_user.tenant_id,
                SupplierReadiness.regime == regime,
            )
            .order_by(SupplierReadiness.assessed_at.desc())
            .first()
        )

        # Return existing if less than 1 hour old
        if existing:
            age_seconds = (datetime.utcnow() - existing.assessed_at).total_seconds()
            if age_seconds < 3600:  # 1 hour
                return SupplierReadinessResponse(
                    id=str(existing.id),
                    tenant_id=existing.tenant_id,
                    regime=existing.regime,
                    overall_band=existing.overall_band.value,
                    dimension_scores=existing.dimension_scores,
                    improvement_actions=existing.improvement_actions,
                    assessed_at=existing.assessed_at,
                    previous_band=existing.previous_band.value if existing.previous_band else None,
                    progress_trend=existing.progress_trend.value if existing.progress_trend else "stable",
                    methodology_version=existing.methodology_version,
                    confidence_level=existing.confidence_level or "medium",
                )

    # Perform new assessment
    result = engine.assess_supplier(
        db,
        tenant_id=current_user.tenant_id,
        regime=regime,
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assess readiness for regime: {regime}"
        )

    return result


@router.get(
    "/passport",
    response_model=CoachingPassport,
    summary="Get multi-regime coaching passport",
    description="""
    Returns readiness summary across all supported regimes.

    Used in dashboard widgets and supplier profile views.
    Shows which regimes have been assessed and overall maturity.
    """,
)
async def get_passport(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get multi-regime coaching passport."""
    engine = get_coaching_engine()
    return engine.get_coaching_passport(db, tenant_id=current_user.tenant_id)


# =============================================================================
# IMPROVEMENT ACTIONS
# =============================================================================

@router.get(
    "/{regime}/actions",
    response_model=ImprovementActionListResponse,
    summary="List improvement actions for a regime",
    description="""
    Returns prioritized improvement actions based on current readiness.

    Actions are sorted by impact (critical > high > medium > low).
    Includes status tracking for started/completed actions.
    """,
)
async def list_actions(
    regime: str,
    status_filter: Optional[ActionStatus] = Query(None, description="Filter by action status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List improvement actions for a regime."""
    if regime not in SUPPORTED_REGIMES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported regime: {regime}. Supported: {SUPPORTED_REGIMES}"
        )

    # Get latest assessment
    assessment = (
        db.query(SupplierReadiness)
        .filter(
            SupplierReadiness.tenant_id == current_user.tenant_id,
            SupplierReadiness.regime == regime,
        )
        .order_by(SupplierReadiness.assessed_at.desc())
        .first()
    )

    if not assessment:
        raise HTTPException(
            status_code=404,
            detail=f"No assessment found for regime: {regime}. Run /coaching/{regime}/assess first."
        )

    # Get action statuses
    ack_records = (
        db.query(CoachingAcknowledgment)
        .filter(
            CoachingAcknowledgment.tenant_id == current_user.tenant_id,
            CoachingAcknowledgment.regime == regime,
        )
        .all()
    )
    action_statuses = {a.action_id: a.status for a in ack_records}

    # Parse actions from assessment
    actions = []
    status_counts = {"pending": 0, "started": 0, "completed": 0, "dismissed": 0}

    for action_data in assessment.improvement_actions:
        action_id = action_data.get("id")
        status = action_statuses.get(action_id, ActionStatus.PENDING)

        # Apply status filter
        if status_filter and status != status_filter:
            continue

        status_counts[status.value] += 1
        action = ImprovementAction(**action_data)
        actions.append(action)

    return ImprovementActionListResponse(
        regime=regime,
        tenant_id=current_user.tenant_id,
        actions=actions,
        total_count=len(actions),
        by_status=status_counts,
    )


@router.post(
    "/actions/{action_id}/status",
    response_model=ActionStatusResponse,
    summary="Update action status",
    description="""
    Update the status of an improvement action.

    Suppliers can mark actions as:
    - started: Work has begun
    - completed: Action is finished
    - dismissed: Not applicable (optional notes encouraged)
    """,
)
async def update_action_status(
    action_id: str,
    update: ActionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update status of an improvement action."""
    # Find or create acknowledgment record
    ack = (
        db.query(CoachingAcknowledgment)
        .filter(
            CoachingAcknowledgment.tenant_id == current_user.tenant_id,
            CoachingAcknowledgment.action_id == action_id,
        )
        .first()
    )

    now = datetime.utcnow()

    if not ack:
        # Extract regime from action_id (e.g., "csrd_add_scope3_categories" -> "csrd")
        regime = action_id.split("_")[0] if "_" in action_id else "unknown"

        ack = CoachingAcknowledgment(
            tenant_id=current_user.tenant_id,
            action_id=action_id,
            regime=regime,
            status=update.status,
            notes=update.notes,
        )
        db.add(ack)

    # Update status and timestamps
    ack.status = update.status
    if update.notes:
        ack.notes = update.notes

    if update.status == ActionStatus.STARTED and not ack.started_at:
        ack.started_at = now
    elif update.status == ActionStatus.COMPLETED:
        ack.completed_at = now
    elif update.status == ActionStatus.DISMISSED:
        ack.dismissed_at = now

    ack.updated_at = now

    db.commit()
    db.refresh(ack)

    return ActionStatusResponse(
        action_id=ack.action_id,
        status=ack.status.value,
        started_at=ack.started_at,
        completed_at=ack.completed_at,
        notes=ack.notes,
        updated_at=ack.updated_at,
    )


# =============================================================================
# EXPORT (Ethics Charter Required)
# =============================================================================

@router.get(
    "/export",
    summary="Export coaching data",
    description="""
    Export all coaching data for the authenticated supplier.

    **Ethics Charter Requirement (Section 1):**
    Coaching data must be exportable in multiple formats.

    Formats:
    - json: Machine-readable JSON with full history
    - pdf: Human-readable improvement plan document
    """,
)
async def export_coaching_data(
    format: Literal["json", "pdf"] = Query("json", description="Export format"),
    include_history: bool = Query(False, description="Include historical assessments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export coaching data (Ethics Charter compliance)."""

    # Get all assessments
    query = db.query(SupplierReadiness).filter(
        SupplierReadiness.tenant_id == current_user.tenant_id,
    )

    if not include_history:
        # Get latest per regime
        assessments = []
        for regime in SUPPORTED_REGIMES:
            latest = (
                query.filter(SupplierReadiness.regime == regime)
                .order_by(SupplierReadiness.assessed_at.desc())
                .first()
            )
            if latest:
                assessments.append(latest)
    else:
        assessments = query.order_by(SupplierReadiness.assessed_at.desc()).all()

    # Get all acknowledgments
    acknowledgments = (
        db.query(CoachingAcknowledgment)
        .filter(CoachingAcknowledgment.tenant_id == current_user.tenant_id)
        .all()
    )

    if format == "json":
        # JSON export
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "tenant_id": current_user.tenant_id,
            "assessments": [
                {
                    "id": a.id,
                    "regime": a.regime,
                    "overall_band": a.overall_band.value,
                    "dimension_scores": a.dimension_scores,
                    "improvement_actions": a.improvement_actions,
                    "assessed_at": a.assessed_at.isoformat() if a.assessed_at else None,
                    "previous_band": a.previous_band.value if a.previous_band else None,
                    "progress_trend": a.progress_trend.value if a.progress_trend else None,
                }
                for a in assessments
            ],
            "action_progress": [
                {
                    "action_id": ack.action_id,
                    "regime": ack.regime,
                    "status": ack.status.value,
                    "started_at": ack.started_at.isoformat() if ack.started_at else None,
                    "completed_at": ack.completed_at.isoformat() if ack.completed_at else None,
                    "notes": ack.notes,
                }
                for ack in acknowledgments
            ],
        }
        return export_data

    elif format == "pdf":
        # PDF export (placeholder - would use reportlab)
        # For now, return structured text that could be rendered as PDF
        content = f"""
COACHING IMPROVEMENT PLAN
=========================
Tenant: {current_user.tenant_id}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

"""
        for assessment in assessments:
            content += f"""
REGIME: {assessment.regime.upper()}
Overall Band: {assessment.overall_band.value.title()}
Assessed: {assessment.assessed_at.strftime('%Y-%m-%d') if assessment.assessed_at else 'N/A'}

Improvement Actions:
"""
            for action in assessment.improvement_actions:
                content += f"""
  - {action.get('title', 'Unknown')}
    Impact: {action.get('impact', 'medium')}
    Effort: {action.get('effort', 'medium')}
    Role: {action.get('suggested_role', 'Team Lead')}
    {action.get('description', '')[:200]}...
"""

        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=coaching_plan_{current_user.tenant_id}.txt"
            }
        )


# =============================================================================
# SUPPORTED REGIMES (Reference)
# =============================================================================

@router.get(
    "/regimes",
    summary="List supported regimes",
    description="Returns list of regimes that have coaching support.",
)
async def list_supported_regimes():
    """List supported regimes for coaching."""
    return {
        "supported_regimes": SUPPORTED_REGIMES,
        "description": {
            "csrd": "Corporate Sustainability Reporting Directive (EU)",
            "cbam": "Carbon Border Adjustment Mechanism (EU)",
            "eudr": "EU Deforestation Regulation",
            "issb": "International Sustainability Standards Board",
        }
    }
