from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class TargetTypeEnum(str, Enum):
    ABSOLUTE = "ABSOLUTE"
    INTENSITY = "INTENSITY"
    NET_ZERO = "NET_ZERO"
    OTHER = "OTHER"

class EmissionAmount(BaseModel):
    value: float
    unit: str = "tCO2e"

class BaseYearReference(BaseModel):
    base_year: int = Field(alias="BaseYear")
    base_year_emissions: EmissionAmount = Field(alias="BaseYearEmissions")
    recalculation_policy: Optional[str] = Field(alias="RecalculationPolicy", default=None)

class TargetReference(BaseModel):
    target_id: str = Field(alias="TargetId")
    target_type: TargetTypeEnum = Field(alias="TargetType")
    target_year: int = Field(alias="TargetYear")
    reduction_percentage: float = Field(alias="ReductionPercentage")
    validation_body: Optional[str] = Field(alias="ValidationBody", default=None)

class ClimateTargets(BaseModel):
    target_reference: List[TargetReference] = Field(alias="TargetReference")
    