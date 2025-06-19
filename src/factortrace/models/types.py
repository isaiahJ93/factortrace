from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional

from factortrace.models.common_enums import (
    GasTypeEnum,
    TierLevelEnum,
    UncertaintyDistributionEnum,
)

class EmissionFactor(BaseModel):
    gas: GasTypeEnum
    value: Decimal = Field(..., ge=0)
    unit: str
    tier: TierLevelEnum
    source: Optional[str] = None
    distribution: Optional[UncertaintyDistributionEnum] = None

class EmissionsRecord(BaseModel):
    activity_name: str
    activity_value: Decimal
    activity_unit: str
    emission_factor: EmissionFactor
    emissions_tco2e: Decimal