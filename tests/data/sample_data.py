from decimal import Decimal
from datetime import date
from factortrace.models import (
    EmissionVoucher,
    EmissionsRecord,
    EmissionFactor,
    GHGBreakdown,
    DataQuality,
    TierLevelEnum,
    GasTypeEnum,
    UncertaintyDistributionEnum,
)

SAMPLE_DATA: dict = {
    "supplier_lei": "5493001KTIIGC8YR12A2",
    "supplier_name": "Acme Metals",
    "supplier_country": "DE",
    "supplier_sector": "steel",
    "reporting_entity_lei": "5493001KTIIGC8YR12A2",
    "reporting_period_start": date(2024, 1, 1),
    "reporting_period_end": date(2024, 12, 31),
    "consolidation_method": "operational_control",
    "emissions_records": [
        {
            "scope": "scope_1",
            "activity_name": "blast_furnace",
            "quantity": 1_000,
            "quantity_unit": "t_hot_metal",
            "emission_factor": {
                "tier": "tier_1",                              # ✔ lowercase enum
                "factor_value": 2.05,
                "factor_unit": "tCO2e/t",
                "reference": "IPCC 2021",
                "data_quality": {
                    "tier": "tier_1",
                    "score": Decimal("92.1"),
                    "temporal_representativeness": 90,
                    "geographical_representativeness": 95,
                    "technological_representativeness": 88,
                    "completeness": 93,
                    "confidence_level": 95,                   # NEW: not None
                    "distribution": "lognormal"              # NEW: enum value
                }
            },
            "ghg_breakdown": [
                {
                    "gas_type": "co2",                        # ✔ lowercase enum
                    "amount": 1800.0,
                    "gwp_factor": 1.0
                },
                {
                    "gas_type": "n2o",
                    "amount": 2.3,
                    "gwp_factor": 265.0
                }
            ]
        }
    ],
    "total_emissions_tco2e": 100.0
}

# Usage in a fixture
def _sample_record() -> dict:
    import copy
    return copy.deepcopy(SAMPLE_DATA["emissions_records"][0])

def sample_voucher() -> EmissionVoucher:
    return EmissionVoucher(**copy.deepcopy(SAMPLE_DATA))