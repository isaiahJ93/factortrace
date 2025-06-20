from enum import Enum

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
    