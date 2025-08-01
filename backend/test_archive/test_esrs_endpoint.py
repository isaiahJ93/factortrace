import sys
import json
sys.path.append('.')

# Import the function directly
from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl

# Test data
test_data = {
    "organization": "Test Company",
    "lei": "TEST123456789012345",
    "reporting_period": 2024,
    "emissions": {
        "scope1": 1000,
        "scope2_location": 500,
        "scope2_market": 400,
    },
    "scope3_detailed": {
        "category_1": {"emissions_tco2e": 5000, "excluded": False, "data_quality_tier": "Tier 2"},
        "category_2": {"emissions_tco2e": 2000, "excluded": False, "data_quality_tier": "Tier 3"},
        "category_3": {"emissions_tco2e": 1500, "excluded": False, "data_quality_tier": "Tier 2"},
    },
    "transition_plan": {
        "adopted": True,
        "net_zero_target_year": 2050,
        "adoption_date": "2024-01-15"
    },
    "governance": {
        "board_oversight": True,
        "board_meetings_climate": 4
    },
    "climate_policy": {
        "has_climate_policy": True,
        "policy_description": "Comprehensive climate policy covering all operations"
    },
    "targets": {
        "base_year": 2020,
        "base_year_emissions": 10000,
        "targets": [
            {
                "description": "Reduce Scope 1 & 2 emissions",
                "target_year": 2030,
                "reduction_percent": 50,
                "progress_percent": 25
            }
        ]
    },
    "energy_consumption": {
        "electricity_mwh": 1000,
        "renewable_electricity_mwh": 300
    }
}

try:
    print("Testing generate_world_class_esrs_e1_ixbrl...")
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    
    print("✓ Function executed successfully!")
    print(f"Result type: {type(result)}")
    print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
    
    # Save the output if it's HTML
    if isinstance(result, dict) and 'report_html' in result:
        filename = f"test_esrs_e1_report_{result.get('document_id', 'test')}.html"
        with open(filename, 'w') as f:
            f.write(result['report_html'])
        print(f"✓ Report saved to {filename}")
        
    # Save the iXBRL if present
    if isinstance(result, dict) and 'ixbrl_content' in result:
        filename = f"test_esrs_e1_{result.get('document_id', 'test')}_inline.xbrl"
        with open(filename, 'w') as f:
            f.write(result['ixbrl_content'])
        print(f"✓ iXBRL saved to {filename}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
