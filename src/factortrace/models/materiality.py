from datetime import date
from factortrace.models.common_enums import (
    TierLevelEnum,
    ConsolidationMethodEnum,
    UncertaintyDistributionEnum,
)
from typing import List, Optional
from enum import Enum 
from pydantic import BaseModel, Field, ConfigDict

# ── enums ───────────────────────────────────────────────────────
class MaterialityType(str, Enum):
    double_materiality = "double_materiality"
    financial_only     = "financial_only"
    impact_only        = "impact_only"


class TimeHorizon(str, Enum):
    SHORT_TERM  = "SHORT_TERM"
    MEDIUM_TERM = "MEDIUM_TERM"
    LONG_TERM   = "LONG_TERM"


class RiskType(str, Enum):
    PHYSICAL   = "PHYSICAL"
    TRANSITION = "TRANSITION"
    OTHER      = "OTHER"

# ── main model ──────────────────────────────────────────────────
class MaterialityAssessment(BaseModel):
    assessment_date: date
    materiality_type: MaterialityType

    # impact side
    impact_score: float
    impact_magnitude: float
    impact_likelihood: float = Field(..., ge=0.0, le=1.0)
    impact_scope: str

    # financial side
    financial_score: float
    financial_impact: float
    financial_likelihood: float = Field(..., ge=0.0, le=1.0)
    financial_time_horizon: TimeHorizon

    # meta
    materiality_threshold: float = Field(..., ge=0.0, le=1.0)
    is_material: bool
    justification: Optional[str] = None
    time_horizon: TimeHorizon
    affected_stakeholders: List[str]
    risk_type: RiskType
    reporting_period: str

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

# ----------------------------------------------------------------