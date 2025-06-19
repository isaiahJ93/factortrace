from __future__ import annotations
from enum import Enum 
from factortrace.models.uncertainty_model import (
    TierLevelEnum,
    ConsolidationMethodEnum,
    UncertaintyDistributionEnum,
)
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class UncertaintyDistributionEnum(str, Enum):
    LOGNORMAL = "LOGNORMAL"
    NORMAL = "NORMAL"
    UNIFORM = "UNIFORM"
    TRIANGULAR = "TRIANGULAR"


    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls.__members__.get(value.upper())

class UncertaintyAssessment(BaseModel):
    uncertainty_percentage: float = Field(alias="UncertaintyPercentage")
    lower_bound: Optional[float] = Field(default=None, alias="LowerBound")
    upper_bound: Optional[float] = Field(default=None, alias="UpperBound")
    confidence_level: float = Field(default=95, alias="ConfidenceLevel")
    distribution: Optional[UncertaintyDistributionEnum] = Field(default=None, alias="Distribution")
    method: Optional[str] = Field(default=None, alias="Method")
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,   # now emits "LOGNORMAL", etc.
    )

__all__ = ["UncertaintyAssessment", "UncertaintyDistributionEnum"]