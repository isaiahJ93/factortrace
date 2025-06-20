from __future__ import annotations
from factortrace.shared_enums import (
    GWPVersionEnum,
    TierLevelEnum,
    Scope3CategoryEnum,
    ScopeLevelEnum,
    VerificationLevelEnum,
    ConsolidationMethodEnum,
    DataQualityTierEnum,
    ValueChainStageEnum,
    UncertaintyDistributionEnum,
    TemporalGranularityEnum,
    GasTypeEnum,

    Scope3CategoryEnum,
    VerificationLevelEnum,
    AuditActionEnum,
    ConsolidationMethodEnum,
    TargetTypeEnum,
    GWPVersionEnum,
)
from enum import Enum

class MaterialityTypeEnum(str, Enum):
    FINANCIAL = "financial"
    IMPACT = "impact"
