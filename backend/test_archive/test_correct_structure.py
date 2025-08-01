import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl, validate_efrag_compliance
import json

# Let's first understand what structure is expected
# by looking at the validation function
print("Checking validation structure...")

# Create test data with nested structure
test_data = {
    # Basic information
    "organization": "Example Corporation Ltd",
    "lei": "5493000KJTIIGC8Y1R12",
    "reporting_period": 2024,
    "consolidation_scope": "Group",
    "headquarters_location": "EU",
    "company_size": "large",
    "sector": "Manufacturing",  # Add missing field
    "primary_nace_code": "C20",  # Add missing field
    
    # Emissions at root level (for E1-6)
    "emissions": {
        "scope1": 15000,
        "scope2_location": 8000,
        "scope2_market": 6500,
        "scope3": 120000,
        "ghg_intensity": 45.2,
        "ghg_breakdown": {  # Add missing field
            "co2": 140000,
            "ch4": 2000,
            "n2o": 1500,
            "hfcs": 0,
            "pfcs": 0,
            "sf6": 0,
            "nf3": 0
        }
    },
    
    # ESRS E1 specific data in nested structure
    "esrs_e1_data": {
        # E1-1: Transition plan
        "transition_plan": {
            "net_zero_target": True,
            "net_zero_target_year": 2050,
            "milestones": [
                {"year": 2030, "target": "50% reduction"},
                {"year": 2040, "target": "80% reduction"}
            ],
            "adopted": True,
            "adoption_date": "2024-01-01"
        },
        
        # E1-2: Governance
        "governance": {
            "board_oversight": True,
            "governance_integration": "Fully integrated into board governance",
            "climate_expertise": "Board has climate experts"
        },
        
        # E1-3: Actions
        "actions": {
            "capex": 100,
            "opex": 20,
            "fte": 25,
            "climate_actions": [
                {
                    "description": "Solar installation",
                    "investment_meur": 50
                }
            ]
        },
        
        # E1-4: Targets
        "targets": {
            "base_year": 2020,
            "progress": 25,
            "base_year_emissions": 150000,
            "targets": [
                {
                    "description": "50% by 2030",
                    "target_year": 2030,
                    "reduction_percent": 50
                }
            ]
        },
        
        # E1-5: Energy
        "energy_consumption": {
            "total": 100000,
            "renewable_percentage": 28,
            "electricity_mwh": 50000,
            "renewable_electricity_mwh": 20000
        },
        
        # E1-6: Emissions (might need duplication)
        "emissions": {
            "scope1": 15000,
            "scope2": 6500,
            "scope3": 120000,
            "ghg_intensity": 45.2
        }
    },
    
    # Financial effects (E1-9)
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
        "climate_related_costs": 35000000
    },
    
    # Also keep some data at root level as fallback
    "transition_plan": {
        "net_zero_target": True,
        "net_zero_target_year": 2050,
        "milestones": [
            {"year": 2030, "target": "50% reduction"},
            {"year": 2040, "target": "80% reduction"}
        ],
        "adopted": True
    },
    
    "governance": {
        "board_oversight": True,
        "governance_integration": "Fully integrated",
        "climate_expertise": "Yes"
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
        "total": 100000
    },
    
    # Scope 3 details
    "scope3_detailed": {
        f"category_{i}": {
            "emissions_tco2e": 8000 if i < 10 else 7000,
            "excluded": False,
            "data_quality_tier": "Tier 2"
        } for i in range(1, 16)
    },
    
    # Other required fields
    "data_quality_score": 82,
    "emissions_change_percent": -8.5,
    "methodology": {
        "ghg_standard": "GHG Protocol"
    },
    
    # EU Taxonomy with DNSH
    "eu_taxonomy_data": {
        "eligible_activities": [
            {
                "name": "Solar energy generation",
                "dnsh_compliant": True,  # Fix DNSH issue
                "substantial_contribution": True,
                "minimum_safeguards": True
            }
        ]
    }
}

# Test validation
try:
    print("\nRunning validation...")
    validation = validate_efrag_compliance(test_data)
    
    print(f"\nValidation Results:")
    print(f"- Valid: {validation.get('is_valid', False)}")
    print(f"- Completeness: {validation.get('completeness_score', 0)}%")
    print(f"- Errors: {len(validation.get('errors', []))}")
    
    if validation.get('errors'):
        print("\nRemaining errors:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    # Try to generate report
    if validation.get('is_valid') or len(validation.get('errors', [])) < 5:
        print("\nAttempting to generate report...")
        result = generate_world_class_esrs_e1_ixbrl(test_data)
        print("✓ SUCCESS! Report generated!")
    else:
        print("\nToo many validation errors to proceed")
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Save the structure for reference
with open('correct_structure.json', 'w') as f:
    json.dump(test_data, f, indent=2)
print("\n✓ Saved structure to correct_structure.json")
