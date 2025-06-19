# tests/conftest.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

def _sample_record():
    return {
        "scope": "SCOPE_3",
        "value_chain_stage": "downstream",
        "activity_description": "Purchased steel",
        "activity_value": 100,
        "activity_unit": "t",
        "emission_factor": {
            "factor_id": "EF-001",
            "value": 2.1,
            "unit": "tCO2e/t",
            "source": "DEFRA_2024",
            "source_year": 2024,
            "tier": "tier_1"
        },
        "ghg_breakdown": [
            {
                "gas_type": "CO2",
                "amount": 210,
                "gwp_factor": 1,
                "gwp_version": "AR6_100"
            }
        ],
        "total_emissions_tco2e": 210,
        "data_quality": {
            "tier": "tier_1",
            "score": 95,
            "temporal_representativeness": 90,
            "geographical_representativeness": 90,
            "technological_representativeness": 90,
            "completeness": 95,
            "uncertainty_percent": 5
        },
        "calculation_method": "invoice_factor",
        "emission_date_start": "2024-01-01",
        "emission_date_end": "2024-01-31"
    }

