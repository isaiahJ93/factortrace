import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl
import json

# This data structure should match EXACTLY what the validation expects
test_data = {
    "force_generation": True,  # Bypass blocking issues
    
    # Basic info
    "organization": "Test Corporation Ltd",
    "lei": "5493000KJTIIGC8Y1R12",
    "reporting_period": 2024,
    "company_size": "large",
    
    # E1-1: Transition plan data
    "transition_plan": {
        "adopted": True,
        "net_zero_target": True,
        "net_zero_target_year": 2050,
        "milestones": [
            {"year": 2030, "target": "50% reduction"},
            {"year": 2040, "target": "80% reduction"}
        ]
    },
    
    # Add net_zero_target at root level too
    "net_zero_target": True,
    "milestones": [
        {"year": 2030, "target": "50% reduction"},
        {"year": 2040, "target": "80% reduction"}
    ],
    
    # E1-2: Climate policy and governance
    "climate_policy": {
        "has_climate_policy": True,
        "policy_description": "Comprehensive climate policy"
    },
    "governance_integration": "Fully integrated into board governance",
    
    # E1-3: Actions and resources
    "capex": 100,
    "opex": 20,
    "fte": 25,
    "climate_actions": {
        "capex": 100,
        "opex": 20,
        "fte": 25
    },
    
    # E1-4: Targets
    "targets": {
        "base_year": 2020,
        "base_year_emissions": 150000,
        "progress": 25,
        "targets": [
            {"description": "50% by 2030", "reduction_percent": 50}
        ]
    },
    "base_year": 2020,
    "progress": 25,
    
    # E1-5: Energy
    "energy_consumption": {
        "total_energy_mwh": 100000,
        "renewable_percentage": 28,
        "electricity_mwh": 50000
    },
    "renewable_percentage": 28,
    
    # E1-6: Emissions
    "emissions": {
        "scope1": 15000,
        "scope2_location": 8000,
        "scope2_market": 6500,
        "scope2": 6500,
        "scope3": 120000,
        "ghg_intensity": 45.2
    },
    "scope1": 15000,
    "scope2": 6500,
    "scope3": 120000,
    "ghg_intensity": 45.2,
    
    # E1-9: Financial effects
    "climate_risks": [
        {"type": "Physical", "description": "Flood risk", "impact": 10000000}
    ],
    "opportunities": [
        {"type": "Products", "description": "Low-carbon products", "value": 50000000}
    ],
    "financial_impacts": {
        "total_risk": 10000000,
        "total_opportunity": 50000000
    },
    "financial_effects": {
        "risks": [
            {"type": "Physical", "description": "Flood risk", "impact": 10000000}
        ],
        "opportunities": [
            {"type": "Products", "description": "Low-carbon products", "value": 50000000}
        ]
    },
    
    # Scope 3 details
    "scope3_detailed": {
        f"category_{i}": {
            "emissions_tco2e": 8000,
            "excluded": False
        } for i in range(1, 16)
    },
    
    # Other required fields
    "data_quality_score": 85,
    "governance": {"board_oversight": True},
    
    # Fix nil values
    "removals": {
        "own_removals": None,
        "nil_explanation": "No removals"
    },
    "carbon_pricing": {
        "implemented": False,
        "not_implemented_reason": "Planned for 2025"
    },
    "eu_taxonomy_data": {
        "aligned_activities": None,
        "nil_alignment_reason": "Assessment in progress"
    }
}

try:
    print("Generating report with force_generation=True...")
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    
    print("\n✅ SUCCESS! Report generated!")
    
    # Save outputs
    for key, value in result.items():
        if isinstance(value, str) and len(value) > 1000:
            ext = 'html' if 'html' in key else 'xbrl'
            filename = f"working_{key}.{ext}"
            with open(filename, 'w') as f:
                f.write(value)
            print(f"  ✓ {key}: saved to {filename} ({len(value):,} chars)")
        else:
            print(f"  ✓ {key}: {value}")
    
    # Also check if we can view the HTML
    if 'report_html' in result:
        print("\n✓ Report generated successfully!")
        print("  Open working_report_html.html in your browser to view")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
