import sys
sys.path.append('.')

# Temporarily patch the validation function
import app.api.v1.endpoints.esrs_e1_full as esrs_module

# Override the problematic validation
original_validate = esrs_module.validate_efrag_compliance

def patched_validate(data):
    return {
        "is_valid": True,
        "completeness_score": 80,
        "blocking_issues": [],
        "warnings": [],
        "data_quality": {"overall_score": 75}
    }

esrs_module.validate_efrag_compliance = patched_validate

# Now import and test
from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl

# Minimal test data
test_data = {
    "organization": "Test Company Ltd",
    "lei": "5493000KJTIIGC8Y1R12",
    "reporting_period": 2024,
    "emissions": {
        "scope1": 10000,
        "scope2_location": 5000,
        "scope2_market": 4000,
    },
    "scope3_detailed": {
        f"category_{i}": {
            "emissions_tco2e": 1000 * i,
            "excluded": False
        } for i in range(1, 16)
    }
}

try:
    print("Testing with patched validation...")
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    print("✓ Success! Generated report")
    print(f"Keys: {list(result.keys())}")
    
    if 'report_html' in result:
        with open('test_report.html', 'w') as f:
            f.write(result['report_html'])
        print("✓ Saved test_report.html")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
