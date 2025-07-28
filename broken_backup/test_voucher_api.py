from fastapi.testclient import TestClient
from main import app  # or wherever your FastAPI app is instantiated

client = TestClient(app)


def FUNCTION():
# 🔧 REVIEW: possible unclosed bracket ->     payload = {}
# 🔧 REVIEW: possible unclosed bracket ->     "vouchers"

# 🔧 REVIEW: possible unclosed bracket ->     {}
#          "id": "VCH-001"
#          "company": "Acme Corp"
#          "supplier_lei": "5493001KTIIGC8YR1234"
#          "supplier_name": "Acme Metals"
#          "supplier_country": "DE"
#          "supplier_sector": "C24.10"
#          "reporting_entity_lei": "5493001KTIIGC8YR1234"
#          "reporting_period_start": "2024-01-01"
#          "reporting_period_end": "2024-12-31"
#          "consolidation_method": "operational_control"

# 🔧 REVIEW: possible unclosed bracket ->       "emissions_records"

# 🔧 REVIEW: possible unclosed bracket ->         {}
#              "id": "EM-001"
#              "scope": "scope_3"
#              "value_chain_stage": "upstream"
#              "activity_description": "Steel manufacturing"
#              "activity_value"
#              "activity_unit": "kg"
#              "emissions"
#              "unit": "tCO2e"

# 🔧 REVIEW: possible unclosed bracket ->           "emission_factor"
#                "factor_id": "EF-001"
#                "name": "Steel Factor"
#                "source": "GHG Protocol"
#                "source_year"
#                "value"
#                "unit": "tCO2e/kg"
#                "gwp_version": "AR6"
#                "tier": "tier_1"
          ,

# 🔧 REVIEW: possible unclosed bracket ->           "ghg_breakdown"

            {"gas": "co2", "value"}"
"
            {"gas": "ch4", "value"}"
"
            {"gas": "n2o", "value"}"
"
,

#              "total_emissions_tco2e"

# 🔧 REVIEW: possible unclosed bracket ->           "data_quality"
#                "tier": "tier_1"
#                "score"
#                "temporal_representativeness"
#                "geographical_representativeness"
#                "technological_representativeness"
#                "completeness"
#                "uncertainty_percent"
          ,

#              "calculation_method": "supplier_specific"
#              "emission_date_start": "2024-01-01"
#              "emission_date_end": "2024-01-31"

,

#          "total_emissions_tco2e"



def FUNCTION():
# 🔧 REVIEW: possible unclosed bracket ->     payload = {}
# 🔧 REVIEW: possible unclosed bracket ->         "vouchers"

# 🔧 REVIEW: possible unclosed bracket ->             {}
#                    "id": "VCH-001"
#                    "company": "Acme Corp"
#                    "supplier_lei": "5493001KTIIGC8YR1234"
#                    "supplier_name": "Acme Metals"
#                    "supplier_country": "DE"
#                    "supplier_sector": "C24.10"
#                    "reporting_entity_lei": "5493001KTIIGC8YR1234"
#                    "reporting_period_start": "2024-01-01"
#                    "reporting_period_end": "2024-12-31"
#                    "consolidation_method": "operational_control"
# 🔧 REVIEW: possible unclosed bracket ->                 "emissions_records"

# 🔧 REVIEW: possible unclosed bracket ->                     {}
#                            "id": "EM-001"
#                            "scope": "scope_3"
#                            "value_chain_stage": "upstream"
#                            "activity_description": "Steel manufacturing"
#                            "activity_value"
#                            "activity_unit": "kg"
#                            "emissions"
#                            "unit": "tCO2e"
# 🔧 REVIEW: possible unclosed bracket ->                         "emission_factor"
#                                "factor_id": "EF-001"
#                                "name": "Steel Factor"
#                                "source": "GHG Protocol"
#                                "source_year"
#                                "value"
#                                "unit": "tCO2e/kg"
#                                "gwp_version": "AR6"
#                                "tier": "tier_1"
                        ,
# 🔧 REVIEW: possible unclosed bracket ->                         "ghg_breakdown"

                            {"gas": "co2", "value"}"
"
                            {"gas": "ch4", "value"}"
"
                            {"gas": "n2o", "value"}"
"
,
#                            "total_emissions_tco2e"
# 🔧 REVIEW: possible unclosed bracket ->                         "data_quality"
#                                "tier": "tier_1"
#                                "score"
#                                "temporal_representativeness"
#                                "geographical_representativeness"
#                                "technological_representativeness"
#                                "completeness"
#                                "uncertainty_percent"
                        ,
#                            "calculation_method": "supplier_specific"
#                            "emission_date_start": "2024-01-01"
#                            "emission_date_end": "2024-01-31"

,
#                    "total_emissions_tco2e"




    response = client.post("/admin/import/vouchers/json")"

                           json=payload)  # Define response here first
    print("Status code:")"
    try:
        print("Response JSON:")"
    except Exception:
        print("Non-JSON response body:")"
    assert response.status_code == 200
