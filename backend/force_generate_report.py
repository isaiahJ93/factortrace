import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl
import json

# Complete data with force_generation flag
test_data = {
    "force_generation": True,  # This should bypass blocking issues
    
    # All the required data...
    "organization": "Example Corporation Ltd",
    "lei": "5493000KJTIIGC8Y1R12",
    "reporting_period": 2024,
    "company_size": "large",
    
    "emissions": {
        "scope1": 15000,
        "scope2_location": 8000,
        "scope2_market": 6500,
        "scope3": 120000
    },
    
    "scope3_detailed": {
        f"category_{i}": {
            "emissions_tco2e": 8000,
            "excluded": False
        } for i in range(1, 16)
    },
    
    "transition_plan": {
        "adopted": True,
        "net_zero_target_year": 2050
    },
    
    "governance": {
        "board_oversight": True
    },
    
    "data_quality_score": 75
}

try:
    print("Generating report with force_generation=True...")
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    
    print("✓ SUCCESS! Report generated!")
    print(f"\nGenerated outputs:")
    
    for key, value in result.items():
        if isinstance(value, str) and len(value) > 1000:
            filename = f"forced_{key}.html" if 'html' in key else f"forced_{key}.xbrl"
            with open(filename, 'w') as f:
                f.write(value)
            print(f"  - {key}: saved to {filename} ({len(value):,} chars)")
        else:
            print(f"  - {key}: {value}")
            
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
