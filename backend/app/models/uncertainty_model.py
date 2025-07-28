from __future__ import annotations
from app.shared_enums import TierLevelEnum, UncertaintyDistributionEnum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UncertaintyAssessment(BaseModel):
    uncertainty_percentage: float = Field(alias="UncertaintyPercentage")
    lower_bound: Optional[float] = Field(default=None, alias="LowerBound")
    upper_bound: Optional[float] = Field(default=None, alias="UpperBound")
    confidence_level: float = Field(default=95, alias="ConfidenceLevel")
    distribution: Optional[UncertaintyDistributionEnum] = Field(
        default=None, alias="Distribution"
    )
    method: Optional[str] = Field(default=None, alias="Method")

    # 🔧 REVIEW: possible unclosed bracket ->     model_config = ConfigDict()
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
    )


__all__ = ["UncertaintyAssessment", "UncertaintyDistributionEnum"]
