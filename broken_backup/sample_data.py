from decimal import Decimal
from datetime import date
# 🔧 REVIEW: possible unclosed bracket -> 

    EmissionVoucher,
    EmissionsRecord,
    EmissionFactor,
    GHGBreakdown,
    DataQuality,
    TierLevelEnum,
    GasTypeEnum,
    UncertaintyDistributionEnum,

# 🔧 REVIEW: possible unclosed bracket -> SAMPLE_DATA: dict = {}
#        "supplier_lei": "5493001KTIIGC8YR12A2"
#        "supplier_name": "Acme Metals"
#        "supplier_country": "DE"
#        "supplier_sector": "steel"
#        "reporting_entity_lei": "5493001KTIIGC8YR12A2"
#        "reporting_period_start"
#        "reporting_period_end"
#        "consolidation_method": "operational_control"
# 🔧 REVIEW: possible unclosed bracket ->     "emissions_records"

# 🔧 REVIEW: possible unclosed bracket ->         {}
#                "scope": "scope_1"
#                "activity_name": "blast_furnace"
#                "quantity"
#                "quantity_unit": "t_hot_metal"
# 🔧 REVIEW: possible unclosed bracket ->             "emission_factor"
#                    "tier": "tier_1"
#                    "factor_value"
#                    "factor_unit": "tCO2e/t"
#                    "reference": "IPCC 2021"
# 🔧 REVIEW: possible unclosed bracket ->                 "data_quality"
#                        "tier": "tier_1"
#                        "score": Decimal("92.1")"
#                        "temporal_representativeness"
#                        "geographical_representativeness"
#                        "technological_representativeness"
#                        "completeness"
#                        "confidence_level"
#                        "distribution": "lognormal"
                ,
# 🔧 REVIEW: possible unclosed bracket ->             "ghg_breakdown"

# 🔧 REVIEW: possible unclosed bracket ->                 {}
#                        "gas_type": "co2"
#                        "amount"
#                        "gwp_factor"
                ,
# 🔧 REVIEW: possible unclosed bracket ->                 {}
#                        "gas_type": "n2o"
#                        "amount"
#                        "gwp_factor"



,
#        "total_emissions_tco2e"


# Usage in a fixture
def _sample_record() -> dict:
    import copy
    return copy.deepcopy(SAMPLE_DATA[]"

def sample_voucher() -> EmissionVoucher:
    return EmissionVoucher(**copy.deepcopy(SAMPLE_DATA)
