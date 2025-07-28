from factortrace.exporters.xhtml_exporter import generate_ixbrl
from factortrace.models.emissions_voucher import EmissionVoucher


def test_export_voucher_xhtml(tmp_path):
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
                    "factor_id": "EF123",
                    "value": 0.0035,
                    "unit": "kgCO2e/t",
                    "source": "DEFRA",
                    "source_year": 2023,
                    "tier": "tier_1"
                },
                "ghg_breakdown": [
                    {"gas_type": "CO2", "amount": 4000, "gwp_factor": 1.0},
                    {"gas_type": "CH4", "amount": 100, "gwp_factor": 25.0},
                    {"gas_type": "N2O", "amount": 100, "gwp_factor": 298.0}
                ],
                "total_emissions_tco2e": 4.2,
                "data_quality": {
                    "tier": "tier_1",
                    "score": 0.92,
                    "temporal_granularity": "annual",
                    "temporal_representativeness": 0.9,
                    "geographical_representativeness": 0.85,
                    "technological_representativeness": 0.88,
                    "completeness": 0.9,
                    "uncertainty_percent": 5.0,
                    "uncertainty": {
                        "uncertainty_percentage": 5.0,
                        "confidence_level": 95.0,
                        "distribution": "normal"
                    }
                },
                "calculation_method": "factor_based",
                "emission_date_start": "2023-01-01",
                "emission_date_end": "2023-12-31"
            }
        ]
    }

    voucher = EmissionVoucher(**data)
    out_path = tmp_path / "voucher.xhtml"
    generate_ixbrl(voucher, output_path=str(out_path))

    assert out_path.exists()
    content = out_path.read_text()
    assert "<ix:nonFraction" in content

