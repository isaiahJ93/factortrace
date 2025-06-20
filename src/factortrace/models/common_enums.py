from __future__ import annotations
from enum import Enum

class VerificationLevelEnum(str, Enum):
    unverified = "unverified"
    limited = "limited"
    reasonable = "reasonable"

def _ci_missing(cls, value):
    if isinstance(value, str):
        return cls._value2member_map_.get(value.lower())
    return None


for _name in (
    "TierLevelEnum",
    "DataQualityTierEnum",
    "ConsolidationMethodEnum",
    "Scope3CategoryEnum",
    if _name in globals():                      # safe if some enums don’t exist
        setattr(globals()[_name], "_missing_", classmethod(_ci_missing))

class TierLevelEnum(str, Enum):
    tier_1 = "tier_1"
    tier_2 = "tier_2"
    tier_3 = "tier_3"

    @classmethod
    def _missing_(cls, value):
        # allow 'TIER_1' → 'tier_1', etc.
        if isinstance(value, str):
            norm = value.lower()
            for member in cls:
                if member.value == norm:
                    return member
        raise ValueError(f"{value} is not a valid {cls.__name__}")

class _CIEnum(str, Enum):
    """Case-insensitive enum – accepts any spelling, returns test-friendly value."""
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls.__members__.get(value.upper())

# ── distribution ───────────────────────────────────────────────
class UncertaintyDistributionEnum(_CIEnum):
    LOGNORMAL = "LOGNORMAL"
    NORMAL = "NORMAL"
    UNIFORM = "UNIFORM"
    TRIANGULAR = "TRIANGULAR"

# ── tiers ──────────────────────────────────────────────────────
# ── consolidation methods ─────────────────────────────────────
class ConsolidationMethodEnum(_CIEnum):
    EQUITY_SHARE        = "equity_share"
    FINANCIAL_CONTROL   = "financial_control"
    OPERATIONAL_CONTROL = "operational_control"

class GasTypeEnum(str, Enum):
    CO2 = "CO2"
    CH4 = "CH4"
    N2O = "N2O"
    HFC = "HFC"
    PFC = "PFC"
    SF6 = "SF6"
    NF3 = "NF3"

class ValueChainStageEnum(str, Enum):
    upstream = "upstream"
    downstream = "downstream"
    operations = "operations"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls.__members__.get(value.lower())
        
class ScopeLevelEnum(str, Enum):
    scope_1 = "scope_1"
    scope_2 = "scope_2"
    scope_3 = "scope_3"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls.__members__.get(value.lower())
        
from enum import Enum

class Scope3CategoryEnum(str, Enum):
    purchased_goods = "purchased_goods"
    capital_goods = "capital_goods"
    fuel_and_energy = "fuel_and_energy"
    upstream_transport = "upstream_transport"
    waste_generated = "waste_generated"
    business_travel = "business_travel"
    employee_commuting = "employee_commuting"
    upstream_leased_assets = "upstream_leased_assets"
    downstream_transport = "downstream_transport"
    processing_of_sold_products = "processing_of_sold_products"
    use_of_sold_products = "use_of_sold_products"
    end_of_life_treatment = "end_of_life_treatment"
    downstream_leased_assets = "downstream_leased_assets"
    franchises = "franchises"
    investments = "investments"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls.__members__.get(value.lower())
        

class UncertaintyDistributionEnum(str, Enum):
    LOGNORMAL = "LOGNORMAL"
    NORMAL = "NORMAL"
    UNIFORM = "UNIFORM"
    TRIANGULAR = "TRIANGULAR"

# ✅ Add this alias so legacy imports don't break
UncertaintyDistributionEnum = UncertaintyDistributionEnum