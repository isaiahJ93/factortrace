from enum import Enum

# ────────────────────── Enum Definitions ────────────────────── #

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

class VerificationLevelEnum(str, Enum):
    unverified = "unverified"
    limited = "limited"
    reasonable = "reasonable"

class GWPVersionEnum(str, Enum):
    ar4 = "ar4"
    ar5 = "ar5"
    ar6 = "ar6"

class ScopeLevelEnum(str, Enum):  # 👈 this is the one you just added
    scope1 = "scope1"
    scope2 = "scope2"
    scope3 = "scope3"

# ───────────── Lowercase-tolerant missing() hook ───────────── #

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
    "ScopeLevelEnum",  # ✅ include this
):
    if _name in globals():
        setattr(globals()[_name], "_missing_", classmethod(_ci_missing))