# app/schemas/coaching.py
"""
Coaching Layer Pydantic Schemas.

API request/response schemas for supplier readiness assessment
and improvement action tracking.

Ethics Charter Compliance:
- NO numerical scores exposed (bands only)
- EVERY response includes improvement_actions[]
- Rationale REQUIRED for all dimension scores
- Language is growth-focused, not punitive

See docs/features/coaching-layer.md for specification.
See docs/product/ethics-incentives.md for binding constraints.
"""
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMS AS LITERALS (for API schema clarity)
# =============================================================================

ReadinessBandType = Literal["foundational", "emerging", "advanced", "leader"]
DimensionTypeValue = Literal[
    "data_coverage",
    "methodology_quality",
    "governance_maturity",
    "audit_trail_strength"
]
ProgressTrendType = Literal["improving", "stable", "declining"]
EffortLevelType = Literal["low", "medium", "high"]
ImpactLevelType = Literal["low", "medium", "high", "critical"]
ActionStatusType = Literal["pending", "started", "completed", "dismissed"]


# =============================================================================
# DIMENSION SCORE (per-axis assessment)
# =============================================================================

class DimensionScore(BaseModel):
    """
    Score for a single assessment dimension.

    Ethics: score_raw is NEVER included - bands only.
    """
    dimension: DimensionTypeValue
    band: ReadinessBandType
    rationale: str = Field(
        ...,
        min_length=10,
        description="REQUIRED: Explain WHY this band was assigned. "
                    "E.g., 'Coverage at 45%. Add Scope 3 Categories 1 and 4 to reach Advanced (70%).'"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "dimension": "data_coverage",
                "band": "emerging",
                "rationale": "Coverage at 45%. Add Scope 3 Categories 1 and 4 to reach Advanced (70%)."
            }
        }
    }


# =============================================================================
# IMPROVEMENT ACTION
# =============================================================================

class ImprovementAction(BaseModel):
    """
    A specific improvement action for the supplier.

    Ethics: Actions are constructive suggestions, not demands.
    Language uses "Consider" or "To advance, you could" not "You must".
    """
    id: str = Field(..., description="Unique action identifier")
    regime: str = Field(..., description="Regime this action applies to (csrd, cbam, eudr, issb)")
    dimension: DimensionTypeValue
    title: str = Field(..., max_length=100)
    description: str = Field(
        ...,
        description="Actionable guidance using growth-focused language"
    )
    effort: EffortLevelType
    impact: ImpactLevelType
    suggested_role: str = Field(
        ...,
        description="Recommended role to own this action (e.g., 'Sustainability Lead', 'Finance')"
    )
    prerequisites: List[str] = Field(
        default=[],
        description="Action IDs that should be completed first"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "csrd_add_scope3_categories",
                "regime": "csrd",
                "dimension": "data_coverage",
                "title": "Add Core Scope 3 Categories",
                "description": "Consider starting with Categories 1 (Purchased Goods), 4 (Transport), "
                               "and 6 (Business Travel) to establish baseline coverage.",
                "effort": "medium",
                "impact": "high",
                "suggested_role": "Sustainability Lead",
                "prerequisites": []
            }
        }
    }


# =============================================================================
# SUPPLIER READINESS (main assessment response)
# =============================================================================

class SupplierReadinessResponse(BaseModel):
    """
    API response for readiness assessment.

    Ethics Charter Compliance:
    - Uses bands, NOT numerical scores
    - improvement_actions is REQUIRED and must have at least 1 item
    - All dimension_scores include rationale
    """
    id: str
    tenant_id: str
    regime: str
    overall_band: ReadinessBandType
    dimension_scores: List[DimensionScore] = Field(
        ...,
        min_length=1,
        description="Assessment for each dimension with rationale"
    )
    improvement_actions: List[ImprovementAction] = Field(
        ...,
        min_length=1,
        description="REQUIRED: Prioritized actions to advance readiness"
    )
    assessed_at: datetime
    previous_band: Optional[ReadinessBandType] = None
    progress_trend: ProgressTrendType = "stable"
    methodology_version: Optional[str] = None
    confidence_level: Literal["low", "medium", "high"] = "medium"

    @field_validator("improvement_actions")
    @classmethod
    def ensure_actions_exist(cls, v):
        """Ethics Charter: Every assessment MUST include improvement actions."""
        if not v or len(v) == 0:
            raise ValueError(
                "Ethics violation: improvement_actions cannot be empty. "
                "Every assessment must include at least one improvement action."
            )
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "uuid",
                "tenant_id": "uuid",
                "regime": "csrd",
                "overall_band": "emerging",
                "dimension_scores": [
                    {
                        "dimension": "data_coverage",
                        "band": "emerging",
                        "rationale": "Coverage at 45%. Add Scope 3 Categories 1 and 4 to reach Advanced (70%)."
                    }
                ],
                "improvement_actions": [
                    {
                        "id": "csrd_add_scope3_categories",
                        "regime": "csrd",
                        "dimension": "data_coverage",
                        "title": "Add Core Scope 3 Categories",
                        "description": "Consider starting with Categories 1 and 4.",
                        "effort": "medium",
                        "impact": "high",
                        "suggested_role": "Sustainability Lead",
                        "prerequisites": []
                    }
                ],
                "assessed_at": "2025-12-13T10:30:00Z",
                "previous_band": "foundational",
                "progress_trend": "improving",
                "methodology_version": "1.0",
                "confidence_level": "medium"
            }
        }
    }


# =============================================================================
# COACHING PASSPORT (multi-regime summary)
# =============================================================================

class RegimeSummary(BaseModel):
    """Summary of readiness for a single regime."""
    regime: str
    band: Optional[ReadinessBandType] = None
    trend: Optional[ProgressTrendType] = None
    last_assessed: Optional[datetime] = None


class CoachingPassport(BaseModel):
    """
    Multi-regime readiness summary for supplier profile.

    Used in dashboard widgets and supplier passport views.
    """
    tenant_id: str
    regimes: List[RegimeSummary]
    overall_maturity: Optional[ReadinessBandType] = None
    last_assessed: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "tenant_id": "uuid",
                "regimes": [
                    {"regime": "csrd", "band": "emerging", "trend": "improving"},
                    {"regime": "cbam", "band": "foundational", "trend": "stable"},
                    {"regime": "eudr", "band": None, "trend": None},
                    {"regime": "issb", "band": None, "trend": None}
                ],
                "overall_maturity": "emerging",
                "last_assessed": "2025-12-13T10:30:00Z"
            }
        }
    }


# =============================================================================
# ACTION STATUS UPDATE
# =============================================================================

class ActionStatusUpdate(BaseModel):
    """Request to update an improvement action's status."""
    status: ActionStatusType
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional notes from the supplier"
    )


class ActionStatusResponse(BaseModel):
    """Response after updating action status."""
    action_id: str
    status: ActionStatusType
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    updated_at: datetime


# =============================================================================
# NARRATIVE REQUEST (LLM coaching text)
# =============================================================================

class NarrativeRequest(BaseModel):
    """Request for LLM-generated coaching narrative."""
    persona: Literal["cfo", "sustainability_lead", "plant_manager"] = "sustainability_lead"
    focus_areas: Optional[List[DimensionTypeValue]] = None
    time_horizon: Literal["30_days", "90_days", "180_days", "1_year"] = "90_days"


class NarrativeResponse(BaseModel):
    """LLM-generated coaching narrative."""
    narrative: str = Field(
        ...,
        description="Human-friendly coaching text for the specified persona"
    )
    persona: str
    generated_at: datetime
    based_on_assessment: str  # Assessment ID used


# =============================================================================
# EXPORT
# =============================================================================

class CoachingExportRequest(BaseModel):
    """Request parameters for coaching data export."""
    format: Literal["json", "pdf"] = "json"
    include_history: bool = False


# =============================================================================
# LIST RESPONSE
# =============================================================================

class ImprovementActionListResponse(BaseModel):
    """List of improvement actions with metadata."""
    regime: str
    tenant_id: str
    actions: List[ImprovementAction]
    total_count: int
    by_status: dict  # {"pending": 3, "started": 1, "completed": 5}


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Types
    "ReadinessBandType",
    "DimensionTypeValue",
    "ProgressTrendType",
    "EffortLevelType",
    "ImpactLevelType",
    "ActionStatusType",
    # Schemas
    "DimensionScore",
    "ImprovementAction",
    "SupplierReadinessResponse",
    "RegimeSummary",
    "CoachingPassport",
    "ActionStatusUpdate",
    "ActionStatusResponse",
    "NarrativeRequest",
    "NarrativeResponse",
    "CoachingExportRequest",
    "ImprovementActionListResponse",
]
