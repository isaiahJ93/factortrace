from enum import Enum

class TierLevelEnum(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"

class UncertaintyDistributionEnum(str, Enum):
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    TRIANGULAR = "triangular"
    UNIFORM = "uniform"
