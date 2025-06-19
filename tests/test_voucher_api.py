from fastapi.testclient import TestClient
from main import app  # or wherever your FastAPI app is instantiated

client = TestClient(app)

def test_valid_emission_voucher():
    payload = {
    "vouchers": [
    {
      "id": "VCH-001",
      "company": "Acme Corp",
      "supplier_lei": "5493001KTIIGC8YR1234",
      "supplier_name": "Acme Metals",
      "supplier_country": "DE",
      "supplier_sector": "C24.10",
      "reporting_entity_lei": "5493001KTIIGC8YR1234",
      "reporting_period_start": "2024-01-01",
      "reporting_period_end": "2024-12-31",
      "consolidation_method": "operational_control",

      "emissions_records": [
        {
          "id": "EM-001",
          "scope": "scope_3",
          "value_chain_stage": "upstream",
          "activity_description": "Steel manufacturing",
          "activity_value": 1000.0,
          "activity_unit": "kg",
          "emissions": 210.0,
          "unit": "tCO2e",

          "emission_factor": {
            "factor_id": "EF-001",
            "name": "Steel Factor",
            "source": "GHG Protocol",
            "source_year": 2023,
            "value": 0.21,
            "unit": "tCO2e/kg",
            "gwp_version": "AR6",
            "tier": "tier_1"
          },

          "ghg_breakdown": [
            { "gas": "co2", "value": 200.0 },
            { "gas": "ch4", "value": 5.0   },
            { "gas": "n2o", "value": 5.0   }
          ],

          "total_emissions_tco2e": 210.0,

          "data_quality": {
            "tier": "tier_1",
            "score": 95.0,
            "temporal_representativeness": 90.0,
            "geographical_representativeness": 90.0,
            "technological_representativeness": 85.0,
            "completeness": 95.0,
            "uncertainty_percent": 5.0      
          },

          "calculation_method": "supplier_specific",
          "emission_date_start": "2024-01-01",
          "emission_date_end": "2024-01-31"
        }
      ],

      "total_emissions_tco2e": 210.0
    }
  ]
}
def test_valid_emission_voucher():
    payload = {
        "vouchers": [
            {
                "id": "VCH-001",
                "company": "Acme Corp",
                "supplier_lei": "5493001KTIIGC8YR1234",
                "supplier_name": "Acme Metals",
                "supplier_country": "DE",
                "supplier_sector": "C24.10",
                "reporting_entity_lei": "5493001KTIIGC8YR1234",
                "reporting_period_start": "2024-01-01",
                "reporting_period_end": "2024-12-31",
                "consolidation_method": "operational_control",
                "emissions_records": [
                    {
                        "id": "EM-001",
                        "scope": "scope_3",
                        "value_chain_stage": "upstream",
                        "activity_description": "Steel manufacturing",
                        "activity_value": 1000.0,
                        "activity_unit": "kg",
                        "emissions": 210.0,
                        "unit": "tCO2e",
                        "emission_factor": {
                            "factor_id": "EF-001",
                            "name": "Steel Factor",
                            "source": "GHG Protocol",
                            "source_year": 2023,
                            "value": 0.21,
                            "unit": "tCO2e/kg",
                            "gwp_version": "AR6",
                            "tier": "tier_1"
                        },
                        "ghg_breakdown": [
                            {"gas": "co2", "value": 200.0},
                            {"gas": "ch4", "value": 5.0},
                            {"gas": "n2o", "value": 5.0}
                        ],
                        "total_emissions_tco2e": 210.0,
                        "data_quality": {
                            "tier": "tier_1",
                            "score": 95.0,
                            "temporal_representativeness": 90.0,
                            "geographical_representativeness": 90.0,
                            "technological_representativeness": 85.0,
                            "completeness": 95.0,
                            "uncertainty_percent": 5.0
                        },
                        "calculation_method": "supplier_specific",
                        "emission_date_start": "2024-01-01",
                        "emission_date_end": "2024-01-31"
                    }
                ],
                "total_emissions_tco2e": 210.0
            }
        ]
    }

    response = client.post("/admin/import/vouchers/json", json=payload)  # Define response here first
    print("Status code:", response.status_code)
    try:
        print("Response JSON:", response.json())
    except Exception:
        print("Non-JSON response body:", response.content)
    assert response.status_code == 200