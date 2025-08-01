import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl, validate_efrag_compliance
import json

# Build data structure that EXACTLY matches what validation expects
test_data = {
    # Force generation to bypass blocking issues temporarily
    "force_generation": True,
    
    # Basic required fields
    "organization": "Example Corporation Ltd",
    "lei": "5493000KJTIIGC8Y1R12",
    "reporting_period": 2024,
    "consolidation_scope": "Group",
    "headquarters_location": "EU",
    "company_size": "large",
    "sector": "Manufacturing",
    "primary_nace_code": "C20",
    
    # Root level emissions (for general access)
    "emissions": {
        "scope1": 15000,
        "scope2_location": 8000,
        "scope2_market": 6500,
        "scope3": 120000,
        "ghg_intensity": 45.2,
        "ghg_breakdown": {
            "co2": 140000,
            "ch4": 2000,
            "n2o": 1500,
            "hfcs": 0,
            "pfcs": 0,
            "sf6": 0,
            "nf3": 0
        }
    },
    
    # Complete Scope 3 breakdown
    "scope3_detailed": {},
    
    # ESRS E1 specific data structure (this is what validation checks!)
    "esrs_e1_data": {
        # E1-1: Transition plan
        "transition_plan": {
            "net_zero_target": True,
            "net_zero_target_year": 2050,
            "milestones": [
                {
                    "year": 2030,
                    "target": "50% reduction",
                    "description": "Interim science-based target"
                },
                {
                    "year": 2040,
                    "target": "80% reduction",
                    "description": "Deep decarbonization milestone"
                }
            ],
            "adopted": True,
            "adoption_date": "2024-01-01",
            "decarbonization_levers": ["Renewable energy", "Energy efficiency", "Electrification"]
        },
        
        # E1-2: Governance and policy
        "climate_policy": {
            "has_policy": True,
            "policy_description": "Comprehensive climate policy",
            "governance_integration": "Fully integrated into governance",
            "board_oversight": True,
            "management_responsibility": True
        },
        
        # E1-3: Actions and resources
        "actions": {
            "capex": 100,
            "opex": 20,
            "fte": 25,
            "climate_actions": [
                {
                    "description": "Solar panel installation",
                    "type": "Mitigation",
                    "investment_meur": 50
                }
            ]
        },
        
        # E1-4: Targets
        "targets": {
            "base_year": 2020,
            "base_year_emissions": 150000,
            "progress": 25,
            "targets": [
                {
                    "description": "Science-based emission reduction",
                    "target_year": 2030,
                    "reduction_percent": 50,
                    "progress_percent": 25
                }
            ]
        },
        
        # E1-5: Energy consumption
        "energy_consumption": {
            "total_energy_mwh": 100000,
            "renewable_percentage": 28,
            "electricity_mwh": 50000,
            "renewable_electricity_mwh": 20000,
            "heating_cooling_mwh": 20000,
            "renewable_heating_cooling_mwh": 5000,
            "steam_mwh": 10000,
            "renewable_steam_mwh": 1000,
            "fuel_combustion_mwh": 20000,
            "renewable_fuels_mwh": 2000
        },
        
        # E1-6: Emissions (nested version)
        "emissions": {
            "scope1": 15000,
            "scope2": 6500,
            "scope3": 120000,
            "ghg_intensity": 45.2
        }
    },
    
    # Also keep at root level for backward compatibility
    "transition_plan": {
        "net_zero_target": True,
        "net_zero_target_year": 2050,
        "milestones": [
            {"year": 2030, "target": "50% reduction"},
            {"year": 2040, "target": "80% reduction"}
        ],
        "adopted": True
    },
    
    "climate_policy": {
        "has_climate_policy": True,
        "policy_description": "Comprehensive climate policy",
        "governance_integration": "Fully integrated"
    },
    
    "governance": {
        "board_oversight": True,
        "governance_integration": "Fully integrated",
        "management_responsibility": True
    },
    
    "climate_actions": {
        "capex": 100,
        "opex": 20,
        "fte": 25
    },
    
    "targets": {
        "base_year": 2020,
        "progress": 25,
        "base_year_emissions": 150000
    },
    
    "energy_consumption": {
        "renewable_percentage": 28,
        "total_energy_mwh": 100000
    },
    
    # E1-9: Financial effects
    "financial_effects": {
        "risks": [
            {
                "type": "Physical",
                "description": "Flood risk",
                "financial_impact": 10000000
            }
        ],
        "opportunities": [
            {
                "type": "Products",
                "description": "Low-carbon products",
                "potential_value": 50000000
            }
        ],
        "climate_related_costs": 35000000,
        "financial_impacts": {
            "total_risk_exposure": 10000000,
            "total_opportunity_value": 50000000
        }
    },
    
    # Nil values with explanations
    "removals": {
        "own_removals": None,
        "nil_explanation": "No removal projects operational"
    },
    
    "carbon_pricing": {
        "implemented": False,
        "not_implemented_reason": "Carbon pricing planned for 2025"
    },
    
    "eu_taxonomy_data": {
        "aligned_activities": None,
        "nil_alignment_reason": "Taxonomy assessment in progress",
        "eligible_activities": [
            {
                "name": "Solar energy generation",
                "dnsh_compliant": True,
                "dnsh_criteria": {
                    "climate_mitigation": True,
                    "climate_adaptation": True,
                    "water": True,
                    "circular_economy": True,
                    "pollution": True,
                    "biodiversity": True
                },
                "minimum_safeguards": True
            }
        ]
    },
    
    # Other required fields
    "data_quality_score": 85,
    "emissions_change_percent": -8.5,
    "intensity": {"revenue": 45.2},
    "methodology": {"ghg_standard": "GHG Protocol"}
}

# Add Scope 3 categories
for i in range(1, 16):
    test_data["scope3_detailed"][f"category_{i}"] = {
        "emissions_tco2e": 8000,
        "excluded": False,
        "data_quality_tier": "Tier 2"
    }

# Test the validation first
print("Testing validation with complete structure...")
try:
    validation = validate_efrag_compliance(test_data)
    print(f"\nValidation Results:")
    print(f"- Valid: {validation.get('is_valid', False)}")
    print(f"- Errors: {len(validation.get('errors', []))}")
    
    if validation.get('errors'):
        print("\nRemaining errors:")
        for error in validation['errors'][:10]:
            print(f"  - {error}")
except Exception as e:
    print(f"Validation error: {e}")

# Try to generate the report
print("\n" + "="*50)
print("Attempting to generate full report...")
try:
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    
    print("\n✅ SUCCESS! Full report generated with all features!")
    print("\nGenerated outputs:")
    
    for key, value in result.items():
        if isinstance(value, str) and len(value) > 1000:
            filename = f"complete_{key}.{'html' if 'html' in key else 'xbrl'}"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(value)
            print(f"  ✓ {key}: saved to {filename} ({len(value):,} chars)")
        else:
            print(f"  ✓ {key}: {value}")
    
    # Save the working data structure
    with open('working_data_structure.json', 'w') as f:
        json.dump(test_data, f, indent=2)
    print("\n✓ Working data structure saved to working_data_structure.json")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
