from factortrace.models.emissions_voucher import EmissionVoucher

def test_emission_voucher_parses():
    data = {
        "supplier_lei": "5493001KJTIIGC8Y1R12",
        "supplier_name": "Test Supplier Ltd",
        "supplier_country": "AU",
        "supplier_sector": "Energy",
        "reporting_entity_lei": "213800D1EI4A5D8B2T46",
        "reporting_period_start": "2023-01-01",
        "reporting_period_end": "2023-12-31",
        "consolidation_method": "operational_control",
        "scope": "SCOPE_3",
        "value_chain_stage": "upstream",
        "total_emissions_tco2e": 4.2,
        "emissions_records": [
            {
                "gas": "CO2",
                "amount": 4200,
                "unit": "kg",
                "source": "test_calc",
                "confidence": 0.95,
                "method_used": "factor_based",
                "activity_description": "Purchased stuff",
                "activity_value": 1200,
                "activity_unit": "t",
                "scope": "SCOPE_3",
                "value_chain_stage": "upstream",
                "emission_factor": {
                    "value": 0.0035,
                    "unit": "kgCO2e/t"
                },
                "ghg_breakdown": {
                    "CO2": 4000,
                    "CH4": 100,
                    "N2O": 100
                },
                "total_emissions_tco2e": 4.2,
                "data_quality": {
                    "tier": "HIGH",
                    "source": "supplier_provided",
                    "confidence_score": 0.95
                },
                "calculation_method": "factor_based",
                "emission_date_start": "2023-01-01",
                "emission_date_end": "2023-12-31"
            }
        ]
    }

    voucher = EmissionVoucher(**data)
    assert voucher.supplier_name == "Test Supplier Ltd"