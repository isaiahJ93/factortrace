from __future__ import annotations
from enum import Enum

# ---------------------
# 🔢 ENUM DEFINITIONS
# ---------------------

class GWPVersionEnum(str, Enum):
    AR4 = "AR4"
    AR5 = "AR5"
    AR6 = "AR6"
    AR6_100 = "AR6_100"

class TierLevelEnum(str, Enum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"

class Scope3CategoryEnum(str, Enum):
    CATEGORY_1 = "Category 1"
    CATEGORY_2 = "Category 2"
    CATEGORY_3 = "Category 3"
    CATEGORY_4 = "Category 4"
    CATEGORY_5 = "Category 5"
    CATEGORY_6 = "Category 6"
    CATEGORY_7 = "Category 7"
    CATEGORY_8 = "Category 8"
    CATEGORY_9 = "Category 9"
    CATEGORY_10 = "Category 10"
    CATEGORY_11 = "Category 11"
    CATEGORY_12 = "Category 12"
    CATEGORY_13 = "Category 13"
    CATEGORY_14 = "Category 14"
    CATEGORY_15 = "Category 15"

class ScopeLevelEnum(str, Enum):
    ORGANIZATION = "organization"
    PRODUCT = "product"

class VerificationLevelEnum(str, Enum):
    LIMITED = "limited"
    REASONABLE = "reasonable"
    NONE = "none"

class ConsolidationMethodEnum(str, Enum):
    EQUITY_SHARE = "equity_share"
    OPERATIONAL_CONTROL = "operational_control"
    FINANCIAL_CONTROL = "financial_control"

class DataQualityTierEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ValueChainStageEnum(str, Enum):
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    OTHER = "other"

class UncertaintyDistributionEnum(str, Enum):
    NORMAL = "normal"
    TRIANGULAR = "triangular"
    UNIFORM = "uniform"
    LOGNORMAL = "lognormal"

class TemporalGranularityEnum(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class GasTypeEnum(str, Enum):
    CO2 = "CO2"
    CH4 = "CH4"
    N2O = "N2O"
    SF6 = "SF6"
    HFCs = "HFCs"
    PFCs = "PFCs"
    NF3 = "NF3"
    OTHER = "other"

# ---------------------
# 🔄 CASE-INSENSITIVE FALLBACKS
# ---------------------

def _ci_missing_(cls, value):
    for member in cls:
        if member.value.lower() == str(value).lower():
            return member
    raise ValueError(f"{value} is not a valid {cls.__name__}")

# Attach _missing_ fallback to all enums above
for _name in list(globals().keys()):
    if _name.endswith("Enum") and isinstance(globals()[_name], type) and issubclass(globals()[_name], Enum):
        setattr(globals()[_name], "_missing_", classmethod(_ci_missing_))

