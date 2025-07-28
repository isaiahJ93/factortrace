import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl

# Complete test data with ALL required fields
test_data = {
    # Basic info
    "organization": "Test Company Ltd",
    "lei": "5493000KJTIIGC8Y1R12",
    "reporting_period": 2024,
    "consolidation_scope": "Individual",
    "headquarters_location": "EU",
    "company_size": "large",
    
    # Complete emissions data
    "emissions": {
        "scope1": 10000,
        "scope2_location": 5000,
        "scope2_market": 4000,
    },
    
    # Previous year for comparisons
    "previous_year_emissions": {
        "scope1": 11000,
        "scope2_location": 5500,
        "scope2_market": 4500
    },
    
    # All 15 Scope 3 categories
    "scope3_detailed": {
        f"category_{i}": {
            "emissions_tco2e": 1000 * i,
            "excluded": False,
            "data_quality_tier": "Tier 2",
            "calculation_method": "Spend-based",
            "coverage_percent": 90,
            "data_quality_score": 75,
            "uncertainty_range": {"low": 900 * i, "high": 1100 * i}
        } for i in range(1, 16)
    },
    
    # Complete transition plan
    "transition_plan": {
        "adopted": True,
        "adoption_date": "2024-01-15",
        "net_zero_target_year": 2050,
        "net_zero_target": True,
        "milestones": [
            {"year": 2030, "target_reduction": 50},
            {"year": 2040, "target_reduction": 80}
        ],
        "decarbonization_levers": ["Renewable energy", "Energy efficiency", "Electrification"],
        "financial_planning": {"capex_allocated": 100},
        "locked_in_emissions": "Analysis of locked-in emissions from existing assets",
        "just_transition": "Just transition plan ensuring fair treatment of workers"
    },
    
    # Complete governance
    "governance": {
        "board_oversight": True,
        "board_meetings_climate": 4,
        "management_responsibility": True,
        "climate_expertise": "Board includes climate scientists and sustainability experts",
        "climate_linked_compensation": True,
        "governance_integration": "Climate fully integrated into governance structures"
    },
    
    # Complete climate policy
    "climate_policy": {
        "has_climate_policy": True,
        "policy_description": "Comprehensive climate policy aligned with Paris Agreement",
        "policy_adoption_date": "2023-01-01",
        "covers_own_operations": True,
        "covers_value_chain": True,
        "covers_products_services": True,
        "integrated_with_strategy": True,
        "governance_integration": "Policy integrated with overall business strategy"
    },
    
    # Complete actions
    "climate_actions": {
        "actions": [
            {
                "description": "Install solar panels",
                "type": "Mitigation",
                "timeline": "2024-2025",
                "investment_meur": 50,
                "expected_impact": "Reduce Scope 2 by 30%"
            }
        ],
        "capex_climate_eur": 100000000,
        "capex": 100,
        "opex_climate_eur": 20000000,
        "opex": 20,
        "fte_dedicated": 25,
        "fte": 25
    },
    
    # Complete targets
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
                "progress": 25,
                "status": "On track"
            }
        ],
        "sbti_validated": True,
        "sbti_ambition": "1.5°C aligned"
    },
    
    # Complete energy data
    "energy_consumption": {
        "electricity_mwh": 10000,
        "renewable_electricity_mwh": 3000,
        "heating_cooling_mwh": 2000,
        "renewable_heating_cooling_mwh": 500,
        "steam_mwh": 500,
        "renewable_steam_mwh": 100,
        "fuel_combustion_mwh": 5000,
        "renewable_fuels_mwh": 200,
        "energy_intensity_value": 0.5,
        "energy_intensity_unit": "MWh/million EUR",
        "renewable_percentage": 30
    },
    
    # Complete removals (with nil explanations)
    "removals": {
        "total": 0,
        "own_removals": None,
        "nil_explanation": "No removal projects currently operational"
    },
    
    # Complete carbon pricing (with nil explanations)
    "carbon_pricing": {
        "implemented": False,
        "not_implemented_reason": "Internal carbon pricing under development for 2025 implementation"
    },
    
    # Complete EU Taxonomy
    "eu_taxonomy_data": {
        "revenue_aligned_percent": 35,
        "capex_aligned_percent": 45,
        "opex_aligned_percent": 30,
        "aligned_activities": None,
        "nil_alignment_reason": "Taxonomy alignment assessment in progress",
        "eligible_activities": [
            {
                "name": "Solar energy generation",
                "nace_code": "D35.11",
                "revenue_percent": 20,
                "capex_percent": 30,
                "aligned": True
            }
        ]
    },
    
    # Value chain
    "value_chain": {
        "upstream": {
            "suppliers_with_targets_percent": 60,
            "engagement_program": "Supplier Climate Action Program"
        },
        "downstream": {
            "product_carbon_footprints": [
                {
                    "product_name": "Main Product",
                    "carbon_footprint_kg": 10.5,
                    "lca_standard": "ISO 14067"
                }
            ]
        }
    },
    
    # Financial data (E1-9)
    "climate_risks": [
        {
            "type": "Physical",
            "description": "Flood risk to coastal facilities",
            "impact": "Medium",
            "likelihood": "High",
            "financial_impact": 10000000
        }
    ],
    "opportunities": [
        {
            "type": "Products and services",
            "description": "Low-carbon product development",
            "potential_value": 50000000
        }
    ],
    "financial_impacts": {
        "climate_related_costs": 15000000,
        "climate_related_investments": 100000000,
        "climate_related_revenue": 200000000
    },
    
    # Additional metadata
    "data_quality_score": 75,
    "emissions_change_percent": -5.2,
    "intensity": {
        "revenue": 45.2
    },
    "methodology": {
        "ghg_standard": "GHG Protocol Corporate Standard",
        "consolidation_approach": "Operational control",
        "emission_factor_sources": ["DEFRA 2024", "IEA 2024"]
    },
    "uncertainty_assessment": "Monte Carlo analysis shows 95% confidence interval of ±15%",
    "recalculation_policy": "Recalculate base year if structural changes exceed 5% threshold",
    "assurance": {
        "level": "Limited assurance",
        "provider": "PwC",
        "standard": "ISAE 3410",
        "scope": ["Scope 1", "Scope 2", "Scope 3 Categories 1-3"]
    }
}

try:
    print("Testing with complete data...")
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    
    print("✓ Success! Report generated")
    print(f"Result keys: {list(result.keys())}")
    
    # Save outputs
    if 'report_html' in result:
        with open('esrs_e1_report.html', 'w') as f:
            f.write(result['report_html'])
        print("✓ Saved to esrs_e1_report.html")
        
    if 'ixbrl_content' in result:
        with open('esrs_e1_report.xbrl', 'w') as f:
            f.write(result['ixbrl_content'])
        print("✓ Saved to esrs_e1_report.xbrl")
        
    print(f"\nDocument ID: {result.get('document_id')}")
    print(f"Validation score: {result.get('validation', {}).get('completeness_score')}%")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
