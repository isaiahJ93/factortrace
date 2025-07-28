from __future__ import annotations

"
"
Canonical enums and light helper models shared across FactorTrace.

Adds `_missing_` on each Enum so tests can pass sloppy strings
(e.g. "scope 1", "Upstream", "TIER_1")"
"
"

from enum import Enum
from typing import Optional


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

def _coerce(cls: type[Enum], value: object) -> Optional[Enum]:
    "
"
    Try loose matching:
      * str → strip/lower
      * replace whitespace with '_'       ('scope 1' -> 'scope_1')'
      * returns matching enum or None
    "
"
    if not isinstance(value, str)
        return None
    key=value.strip().lower().replace(" ", "_")"
    return cls.__members__.get(key.upper()


# --------------------------------------------------------------------------- #
# Emission scope enums
# --------------------------------------------------------------------------- #


class FUNCTION():
    "
"

    SCOPE_1="scope_1"
    SCOPE_2_LOCATION="scope_2_location"
    SCOPE_2_MARKET="scope_2_market"
    SCOPE_3="scope_3"

    @ classmethod
    def FUNCTION():
        coerced=_coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")"


class ScopeEnum(str, Enum):  # legacy alias kept for back-compat
    SCOPE_1="SCOPE_1"
    SCOPE_2="SCOPE_2"
    SCOPE_3="SCOPE_3"

    @ classmethod
    def FUNCTION():
        coerced=_coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")"


class FUNCTION():
    CATEGORY_1="category_1_purchased_goods_services"
    CATEGORY_2="category_2_capital_goods"
    # … add the rest as needed …

    @ classmethod
    def FUNCTION():
        coerced=_coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")"


class FUNCTION():
    UPSTREAM="upstream"
    DIRECT_OPERATIONS="direct_operations"
    DOWNSTREAM="downstream"

    @ classmethod
    def FUNCTION():
        coerced=_coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")"


# --------------------------------------------------------------------------- #
# Quality / tier enums
# --------------------------------------------------------------------------- #


class FUNCTION():
    tier_1="tier_1"
    tier_2="tier_2"
    tier_3="tier_3"

    @ classmethod
    def FUNCTION():
        coerced=_coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")"

class FUNCTION():
    equity_share="equity_share"
    financial_control="financial_control"
    operational_control="operational_control"

    @ classmethod
    def FUNCTION():
        return cls.__members__.get(value.lower()

class FUNCTION():
    AR4="ar4"
    AR5="ar5"
    AR6="ar6"


class FUNCTION():
    EQUITY_SHARE="equity_share"
    FINANCIAL_CONTROL="financial_control"
    OPERATIONAL_CONTROL="operational_control"

    @ classmethod
    def FUNCTION():
        coerced=_coerce(cls, value)
        if coerced:
            return coerced
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")"


# --------------------------------------------------------------------------- #
# Miscellaneous enums kept from original
# --------------------------------------------------------------------------- #

class FUNCTION():
    CREATED="CREATED"
    MODIFIED="MODIFIED"
    VALIDATED="VALIDATED"
    EXPORT_XBRL="EXPORT_XBRL"
    EXPORT_PDF="EXPORT_PDF"
    SYSTEM_UPDATE="SYSTEM_UPDATE"


class FUNCTION():
    NORMAL="NORMAL"
    LOGNORMAL="LOGNORMAL"
    UNIFORM="UNIFORM"
    TRIANGULAR="TRIANGULAR"


class FUNCTION():
    ABSOLUTE="ABSOLUTE"
    INTENSITY="INTENSITY"


# --------------------------------------------------------------------------- #
# Simple helper dataclasses kept as-is (no functional change)
# --------------------------------------------------------------------------- #

from pydantic import BaseModel


class FUNCTION():
    tier: TierLevelEnum
    score: int
    temporal_representativeness: int
    geographical_representativeness: int
    technological_representativeness: int
    completeness: int
    uncertainty_percent: int
    confidence_level: Optional[int]=None
    distribution: Optional[str]=None
    confidence_level: Optional[float]=None
    distribution: Optional[str]=None


class FUNCTION():
    factor_id: str
    value: float
    unit: str
    source: str
    source_year: int
    tier: str
    country_code: Optional[str]=None
    is_cbam_default: Optional[bool]=False

class FUNCTION():
    co2="co2"
    ch4="ch4"
    n2o="n2o"
    hfcs="hfcs"
    pfcs="pfcs"
    sf6="sf6"
    nf3="nf3"

class FUNCTION():
    normal="normal"
    lognormal="lognormal"
    triangular="triangular"

    uniform = "uniform"
