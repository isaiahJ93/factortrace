from enum import Enum

# ─────────────────── Core Enums ─────────────────── #

class TierLevelEnum(str, Enum):
    tier_1 = "tier_1"
    tier_2 = "tier_2"
    tier_3 = "tier_3"

class DataQualityTierEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class ConsolidationMethodEnum(str, Enum):
    operational_control = "operational_control"
    financial_control = "financial_control"
    equity_share = "equity_share"

class Scope3CategoryEnum(str, Enum):
    purchased_goods = "purchased_goods"
    capital_goods = "capital_goods"
    upstream_transport = "upstream_transport"
    downstream_transport = "downstream_transport"
    business_travel = "business_travel"

class VerificationLevelEnum(str, Enum):
    unverified = "unverified"
    limited = "limited"
    reasonable = "reasonable"

class GWPVersionEnum(str, Enum):
    ar4 = "ar4"
    ar5 = "ar5"
    ar6 = "ar6"

class ScopeLevelEnum(str, Enum):
    scope1 = "scope1"
    scope2 = "scope2"
    scope3 = "scope3"

class ValueChainStageEnum(str, Enum):
    upstream = "upstream"
    operations = "operations"
    downstream = "downstream"

class UncertaintyDistributionEnum(str, Enum):
    triangular = "triangular"
    normal = "normal"
    uniform = "uniform"

class TargetTypeEnum(str, Enum):
    absolute = "absolute"
    intensity = "intensity"

class AuditActionEnum(str, Enum):
    created = "created"
    updated = "updated"
    deleted = "deleted"

class MaterialityTypeEnum(str, Enum):
    quantitative = "quantitative"
    qualitative = "qualitative"

class GasTypeEnum(str, Enum):
    co2 = "co2"
    ch4 = "ch4"
    n2o = "n2o"
    sf6 = "sf6"

class ScopeEnum(str, Enum):
    scope1 = "scope1"
    scope2 = "scope2"
    scope3 = "scope3"

# ───────────── Optional: lowercase _missing_ patch ───────────── #

def _ci_missing(cls, value):
    if isinstance(value, str):
        return cls._value2member_map_.get(value.lower())
    return None

for _name in (
    "TierLevelEnum",
    "DataQualityTierEnum",
    "ConsolidationMethodEnum",
    "Scope3CategoryEnum",
    "VerificationLevelEnum",
    "GWPVersionEnum",
    "ScopeLevelEnum",
    "ValueChainStageEnum",
    "UncertaintyDistributionEnum",
    "TargetTypeEnum",
    "AuditActionEnum",
    "MaterialityTypeEnum",
    "GasTypeEnum",
    "ScopeEnum",
):
    if _name in globals():
        setattr(globals()[_name], "_missing_", classmethod(_ci_missing))