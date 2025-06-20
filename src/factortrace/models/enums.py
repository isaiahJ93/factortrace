"""
Canonical enums and light helper models shared across FactorTrace.

Adds `_missing_` on each Enum so tests can pass sloppy strings
(e.g. "scope 1", "Upstream", "TIER_1") without touching fixtures.
"""
from enum import Enum
from __future__ import annotations
from factortrace.shared_enums import TierLevelEnum
from typing import Optional

# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #


def _coerce(cls: type[Enum], value: object) -> Optional[Enum]:
    """
    Try loose matching:
      • str → strip/lower
      • replace whitespace with '_'       ('scope 1' -> 'scope_1')
      • returns matching enum or None
    """
    if not isinstance(value, str):
        return None
    key = value.strip().lower().replace(" ", "_")
    return cls.__members__.get(key.upper())


# --------------------------------------------------------------------------- #
# Emission scope enums
# --------------------------------------------------------------------------- #


class ScopeLevelEnum(str, Enum):
    """GHG Protocol emission scopes per ESRS E1-6 §44"""

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
    # … add the rest as needed …

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
    tier_1 = "tier_1"
    tier_2 = "tier_2"
    tier_3 = "tier_3"

    @classmethod
    def _missing_(cls, value):
        coerced = _coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")

class ConsolidationMethodEnum(str, Enum):
    equity_share = "equity_share"
    financial_control = "financial_control"
    operational_control = "operational_control"

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

class AuditActionEnum(str, Enum):
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


class TargetTypeEnum(str, Enum):
    ABSOLUTE = "ABSOLUTE"
    INTENSITY = "INTENSITY"


# --------------------------------------------------------------------------- #
# Simple helper dataclasses kept as-is (no functional change)
# --------------------------------------------------------------------------- #

from pydantic import BaseModel


class DataQuality(BaseModel):
    tier: TierLevelEnum
    score: int
    temporal_representativeness: int
    geographical_representativeness: int
    technological_representativeness: int
    completeness: int
    uncertainty_percent: int
    confidence_level: Optional[int] = None
    distribution: Optional[str] = None
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
    co2 = "co2"
    ch4 = "ch4"
    n2o = "n2o"
    hfcs = "hfcs"
    pfcs = "pfcs"
    sf6 = "sf6"
    nf3 = "nf3"

class UncertaintyDistributionEnum(str, Enum):
    normal = "normal"
    lognormal = "lognormal"
    triangular = "triangular"
    uniform = "uniform"