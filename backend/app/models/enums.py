from __future__ import annotations

"""
Adds _missing_ on each Enum so tests can pass sloppy strings
(e.g. "scope 1", "Upstream", "TIER_1")
"""

from enum import Enum
from typing import Optional

from app.models.common_enums import (
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
)

def _coerce(cls: type[Enum], value: object) -> Optional[Enum]:
    if not isinstance(value, str):
        return None
    key = value.strip().lower().replace(" ", "_")
    return cls.__members__.get(key.upper())


class ScopeLevelEnum(str, Enum):
    SCOPE_1 = "scope_1"
    SCOPE_2_LOCATION = "scope_2_location"
    SCOPE_2_MARKET = "scope_2_market"
    SCOPE_3 = "scope_3"

    @classmethod
    def _missing_(cls, value):
        coerced = _coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


class ScopeEnum(str, Enum):  # legacy alias kept for back-compat
    SCOPE_1 = "SCOPE_1"
    SCOPE_2 = "SCOPE_2"
    SCOPE_3 = "SCOPE_3"

    @classmethod
    def _missing_(cls, value):
        coerced = _coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


class Scope3CategoryEnum(str, Enum):
    CATEGORY_1 = "category_1_purchased_goods_services"
    CATEGORY_2 = "category_2_capital_goods"
    # ... add the rest as needed ...

    @classmethod
    def _missing_(cls, value):
        coerced = _coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")

class ValueChainStageEnum(str, Enum):
    UPSTREAM = "upstream"
    DIRECT_OPERATIONS = "direct_operations"
    DOWNSTREAM = "downstream"

    @classmethod
    def _missing_(cls, value):
        coerced = _coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


# --------------------------------------------------------------------------- #
# Quality / tier enums
# --------------------------------------------------------------------------- #


class TierLevelEnum(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"

    @classmethod
    def _missing_(cls, value):
        coerced = _coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


class DataQualityTierEnum(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @classmethod
    def _missing_(cls, value):
        return cls.__members__.get(value.lower())


class GWPVersionEnum(str, Enum):
    AR4 = "ar4"
    AR5 = "ar5"
    AR6 = "ar6"


class ConsolidationMethodEnum(str, Enum):
    EQUITY_SHARE = "equity_share"
    FINANCIAL_CONTROL = "financial_control"
    OPERATIONAL_CONTROL = "operational_control"

    @classmethod
    def _missing_(cls, value):
        coerced = _coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


# --------------------------------------------------------------------------- #
# Miscellaneous enums kept from original
# --------------------------------------------------------------------------- #

class EventTypeEnum(str, Enum):
    CREATED = "CREATED"
    MODIFIED = "MODIFIED"
    VALIDATED = "VALIDATED"
    EXPORT_XBRL = "EXPORT_XBRL"
    EXPORT_PDF = "EXPORT_PDF"
    SYSTEM_UPDATE = "SYSTEM_UPDATE"


class UncertaintyDistributionEnum(str, Enum):
    NORMAL = "NORMAL"
    LOGNORMAL = "LOGNORMAL"
    UNIFORM = "UNIFORM"
    TRIANGULAR = "TRIANGULAR"


class TemporalGranularityEnum(str, Enum):
    ABSOLUTE = "ABSOLUTE"
    INTENSITY = "INTENSITY"


# --------------------------------------------------------------------------- #
# Simple helper dataclasses kept as-is (no functional change)
# --------------------------------------------------------------------------- #

from pydantic import BaseModel


class DataQualityIndicator(BaseModel):
    tier: TierLevelEnum
    score: int
    temporal_representativeness: int
    geographical_representativeness: int
    technological_representativeness: int
    completeness: int
    uncertainty_percent: int
    confidence_level: Optional[float] = None
    distribution: Optional[str] = None


class EmissionFactor(BaseModel):
    factor_id: str
    value: float
    unit: str
    source: str
    source_year: int
    tier: str
    country_code: Optional[str] = None
    is_cbam_default: Optional[bool] = False


class GasTypeEnum(str, Enum):
    CO2 = "co2"
    CH4 = "ch4"
    N2O = "n2o"
    HFCS = "hfcs"
    PFCS = "pfcs"
    SF6 = "sf6"
    NF3 = "nf3"


class VerificationLevelEnum(str, Enum):
    UNVERIFIED = "unverified"
    LIMITED = "limited"
    REASONABLE = "reasonable"

