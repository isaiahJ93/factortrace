import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl

# More complete test data with valid LEI
test_data = {
    "organization": "Test Company Ltd",
    "lei": "5493000KJTIIGC8Y1R12",  # Valid 20-character LEI format
    "reporting_period": 2024,
    "consolidation_scope": "Individual",
    "headquarters_location": "EU",
    
    # Complete emissions data
    "emissions": {
        "scope1": 10000,
        "scope2_location": 5000,
        "scope2_market": 4000,
    },
    
    # All 15 Scope 3 categories
    "scope3_detailed": {
        f"category_{i}": {
            "emissions_tco2e": 1000 * i,
            "excluded": False,
            "data_quality_tier": "Tier 2",
            "calculation_method": "Spend-based",
            "coverage_percent": 90,
            "data_quality_score": 75
        } for i in range(1, 16)
    },
    
    # Transition plan
    "transition_plan": {
        "adopted": True,
        "adoption_date": "2024-01-15",
        "net_zero_target_year": 2050,
        "decarbonization_levers": ["Renewable energy", "Energy efficiency", "Electrification"],
        "financial_planning": {"capex_allocated": 100}
    },
    
    # Governance
    "governance": {
        "board_oversight": True,
        "board_meetings_climate": 4,
        "management_responsibility": True,
        "climate_expertise": "Board includes climate scientists and sustainability experts"
    },
    
    # Climate policy
    "climate_policy": {
        "has_climate_policy": True,
        "policy_description": "Comprehensive climate policy aligned with Paris Agreement",
        "policy_adoption_date": "2023-01-01",
        "covers_own_operations": True,
        "covers_value_chain": True
    },
    
    # Targets
    "targets": {
        "base_year": 2020,
        "base_year_emissions": 150000,
        "targets": [
            {
                "description": "Reduce absolute Scope 1 & 2 emissions",
                "scope": "Scope 1 & 2",
                "target_year": 2030,
                "reduction_percent": 50,
                "progress_percent": 25,
                "status": "On track"
            }
        ],
        "sbti_validated": True,
        "sbti_ambition": "1.5°C aligned"
    },
    
    # Energy
    "energy_consumption": {
        "electricity_mwh": 10000,
        "renewable_electricity_mwh": 3000,
        "heating_cooling_mwh": 2000,
        "renewable_heating_cooling_mwh": 500
    },
    
    # Additional required fields
    "data_quality_score": 75,
    "emissions_change_percent": -5.2,
    "intensity": {
        "revenue": 45.2
    },
    
    # Methodology
    "methodology": {
        "ghg_standard": "GHG Protocol Corporate Standard",
        "consolidation_approach": "Operational control"
    },
    
    # EU Taxonomy
    "eu_taxonomy_data": {
        "revenue_aligned_percent": 35,
        "capex_aligned_percent": 45,
        "opex_aligned_percent": 30
    },
    
    # Value chain
    "value_chain": {
        "upstream": {
            "suppliers_with_targets_percent": 60,
            "engagement_program": "Supplier Climate Action Program"
        }
    },
    
    # Assurance
    "assurance": {
        "level": "Limited assurance",
        "provider": "PwC",
        "standard": "ISAE 3410"
    }
}

try:
    print("Testing with complete valid data...")
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    
    print("✓ Function executed successfully!")
    print(f"Result keys: {list(result.keys())}")
    
    # Save outputs
    if 'report_html' in result:
        with open('test_esrs_report.html', 'w') as f:
            f.write(result['report_html'])
        print("✓ HTML report saved to test_esrs_report.html")
        
    if 'ixbrl_content' in result:
        with open('test_esrs_report.xbrl', 'w') as f:
            f.write(result['ixbrl_content'])
        print("✓ iXBRL saved to test_esrs_report.xbrl")
        
    print(f"\nDocument ID: {result.get('document_id')}")
    print(f"Validation passed: {result.get('validation', {}).get('is_valid')}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
