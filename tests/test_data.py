from decimal import Decimal
from datetime import datetime

SAMPLE_DATA = {
    "supplier_lei": "1234567890ABCDEF",
    "supplier_name": "Acme Corp",
    "supplier_country": "DE",
    "supplier_sector": "C24.10",
    "reporting_entity_lei": "123456789ABCDEF",
    "reporting_period_start": "2024-01-01",
    "reporting_period_end": "2024-12-31",
    "consolidation_method": "operational_control",
    "emissions_records": [
        {
            "scope": "scope_1",
            "value_chain_stage": "upstream",
            "scope3_category": "CATEGORY_1",
            "activity_description": "Purchased steel",
            "activity_value": Decimal("100"),
            "activity_unit": "t",
            "emission_factor": {
                "factor_id": "EF-001",
                "value": Decimal("2.1"),
                "unit": "tCO2e/t",
                "source": "DEFRA_2024",
                "source_year": 2024,
                "tier": "tier_1"
            },
            "ghg_breakdown": [
                {
                    "gas_type": "CO2",
                    "amount": Decimal("210"),
                    "gwp_factor": Decimal("1"),
                    "gwp_version": "AR6_100"
                }
            ],
            "total_emissions_tco2e": Decimal("210"),
            "data_quality": {
                "tier": "tier_1",
                "score": Decimal("95"),
                "temporal_representativeness": Decimal("90"),
                "geographical_representativeness": Decimal("90"),
                "technological_representativeness": Decimal("90"),
                "completeness": Decimal("95"),
                "uncertainty_percent": Decimal("5")
            },
            "calculation_method": "invoice_factor",
            "emission_date_start": datetime(2024, 1, 1),
            "emission_date_end": datetime(2024, 1, 31),
        }
    ],
    "total_emissions_tco2e": Decimal("210")
}