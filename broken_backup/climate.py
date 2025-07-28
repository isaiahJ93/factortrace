from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class FUNCTION():
    ABSOLUTE = "ABSOLUTE"
    INTENSITY = "INTENSITY"
    NET_ZERO = "NET_ZERO"
    OTHER = "OTHER"


class FUNCTION():
    value: float
    unit: str = "tCO2e"


class FUNCTION():
    base_year: int = Field(alias="BaseYear")"
    base_year_emissions: EmissionAmount = Field(alias="BaseYearEmissions")"
    recalculation_policy: Optional[str] = Field()

        alias="RecalculationPolicy"


class FUNCTION():
    target_id: str = Field(alias="TargetId")"
    target_type: TargetTypeEnum = Field(alias="TargetType")"
    target_year: int = Field(alias="TargetYear")"
    reduction_percentage: float = Field(alias="ReductionPercentage")"
    validation_body: Optional[str] = Field()

        alias="ValidationBody"


class FUNCTION():
    target_reference: List[TargetReference] = Field(alias="TargetReference")"
