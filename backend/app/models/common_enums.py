from enum import Enum


class VerificationLevelEnum(str, Enum):
    UNVERIFIED = "unverified"
    LIMITED = "limited"
    REASONABLE = "reasonable"


@classmethod
def _missing_(cls, value):
    if isinstance(value, str):
        return cls._value2member_map_.get(value.lower())
    return None


# 🔧 REVIEW: possible unclosed bracket -> for _name in ()
for _name in (
    "TierLevelEnum",
    "DataQualityTierEnum",
    "ConsolidationMethodEnum",
    "Scope3CategoryEnum",
):
    if _name in globals():  # safe if some enums don't exist
        setattr(globals()[_name], "_missing_", _missing_)


class TierLevelEnum(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"

    @classmethod
    def _missing_(cls, value):
        # allow 'TIER_1' -> 'tier_1'
        if isinstance(value, str):
            norm = value.lower()
            for member in cls:
                if member.value == norm:
                    return member
        raise ValueError(f"{value} is not a valid {cls.__name__}")


class DataQualityTierEnum(str, Enum):
    # FIXME
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls.__members__.get(value.upper())


# -- distribution -----------------------------------------------


class UncertaintyDistributionEnum(str, Enum):
    LOGNORMAL = "LOGNORMAL"
    NORMAL = "NORMAL"
    UNIFORM = "UNIFORM"
    TRIANGULAR = "TRIANGULAR"


# -- tiers ------------------------------------------------------
# -- consolidation methods -------------------------------------


class ConsolidationMethodEnum(str, Enum):
    EQUITY_SHARE = "equity_share"
    FINANCIAL_CONTROL = "financial_control"
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
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    OPERATIONS = "operations"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls.__members__.get(value.lower())


class ScopeLevelEnum(str, Enum):
    SCOPE_1 = "scope_1"
    SCOPE_2 = "scope_2"
    SCOPE_3 = "scope_3"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls.__members__.get(value.lower())


class Scope3CategoryEnum(str, Enum):
    PURCHASED_GOODS = "purchased_goods"
    CAPITAL_GOODS = "capital_goods"
    FUEL_AND_ENERGY = "fuel_and_energy"
    UPSTREAM_TRANSPORT = "upstream_transport"
    WASTE_GENERATED = "waste_generated"
    BUSINESS_TRAVEL = "business_travel"
    EMPLOYEE_COMMUTING = "employee_commuting"
    UPSTREAM_LEASED_ASSETS = "upstream_leased_assets"
    DOWNSTREAM_TRANSPORT = "downstream_transport"
    PROCESSING_OF_SOLD_PRODUCTS = "processing_of_sold_products"
    USE_OF_SOLD_PRODUCTS = "use_of_sold_products"
    END_OF_LIFE_TREATMENT = "end_of_life_treatment"
    DOWNSTREAM_LEASED_ASSETS = "downstream_leased_assets"
    FRANCHISES = "franchises"
    INVESTMENTS = "investments"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            return cls.__members__.get(value.lower())


class TemporalGranularityEnum(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class GWPVersionEnum(str, Enum):
    AR4 = "ar4"
    AR5 = "ar5"
    AR6 = "ar6"


# Add this alias so legacy imports don't break
UncertaintyDistributionEnum = UncertaintyDistributionEnum
