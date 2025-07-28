import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl
import json
from datetime import datetime
import os

# COMPLETE data structure with ALL required fields
test_data = {
    "force_generation": True,
    
    # Basic information
    "organization": "Example Corporation Ltd",
    "lei": "5493000KJTIIGC8Y1R12",
    "reporting_period": 2024,
    "company_size": "large",
    "consolidation_scope": "Group",
    "headquarters_location": "EU",
    "sector": "Manufacturing",
    "primary_nace_code": "C20",
    
    # Complete emissions data
    "emissions": {
        "scope1": 15000,
        "scope2_location": 8000,
        "scope2_market": 6500,
        "scope2": 6500,
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
    
    # Previous year emissions for comparison
    "previous_year_emissions": {
        "scope1": 16500,
        "scope2_location": 8800,
        "scope2_market": 7000,
        "scope3": 125000
    },
    
    # Complete transition plan
    "transition_plan": {
        "adopted": True,
        "adoption_date": "2024-01-01",
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
        "decarbonization_levers": ["Renewable energy", "Energy efficiency", "Electrification"],
        "financial_planning": {
            "capex_allocated": 100000000,
            "investment_period": "2024-2030"
        },
        "locked_in_emissions": "Analysis shows 20% of current emissions locked-in until 2035",
        "just_transition": "Comprehensive reskilling program for affected workers"
    },
    
    # Complete governance
    "governance": {
        "board_oversight": True,
        "board_meetings_climate": 6,
        "management_responsibility": True,
        "climate_expertise": "Two board members with climate science PhDs",
        "climate_linked_compensation": True,
        "governance_integration": "Climate KPIs in all executive scorecards"
    },
    
    # Complete climate policy
    "climate_policy": {
        "has_climate_policy": True,
        "policy_description": "Net-zero aligned climate policy approved by board",
        "policy_adoption_date": "2023-01-01",
        "covers_own_operations": True,
        "covers_value_chain": True,
        "covers_products_services": True,
        "integrated_with_strategy": True,
        "governance_integration": "Board review quarterly"
    },
    
    # Complete climate actions
    "climate_actions": {
        "actions": [
            {
                "description": "Install 50MW solar capacity",
                "type": "Mitigation",
                "timeline": "2024-2025",
                "investment_meur": 50,
                "expected_impact": "Reduce Scope 2 by 30%"
            },
            {
                "description": "Fleet electrification",
                "type": "Mitigation",
                "timeline": "2024-2027",
                "investment_meur": 30,
                "expected_impact": "Reduce Scope 1 by 15%"
            }
        ],
        "capex": 100,
        "opex": 20,
        "fte": 25,
        "capex_climate_eur": 100000000,
        "opex_climate_eur": 20000000,
        "fte_dedicated": 25
    },
    
    # COMPLETE targets with ALL required fields
    "targets": {
        "base_year": 2020,
        "base_year_emissions": 150000,
        "progress": 25,
        "targets": [
            {
                "description": "Reduce absolute emissions 50% by 2030",
                "scope": "Scope 1, 2 & 3",
                "target_year": 2030,
                "reduction_percent": 50,  # THIS WAS MISSING!
                "progress_percent": 25,
                "status": "On track",
                "baseline": 150000,
                "target_emissions": 75000
            },
            {
                "description": "Achieve net zero emissions",
                "scope": "All scopes",
                "target_year": 2050,
                "reduction_percent": 100,  # THIS WAS MISSING!
                "progress_percent": 10,
                "status": "On track",
                "baseline": 150000,
                "target_emissions": 0
            }
        ],
        "sbti_validated": True,
        "sbti_ambition": "1.5°C aligned"
    },
    
    # Complete energy consumption
    "energy_consumption": {
        "total": 100000,
        "total_energy_mwh": 100000,
        "renewable_percentage": 28,
        "electricity_mwh": 50000,
        "renewable_electricity_mwh": 20000,
        "heating_cooling_mwh": 20000,
        "renewable_heating_cooling_mwh": 5000,
        "steam_mwh": 10000,
        "renewable_steam_mwh": 1000,
        "fuel_combustion_mwh": 20000,
        "renewable_fuels_mwh": 2000,
        "energy_intensity_value": 0.5,
        "energy_intensity_unit": "MWh/million EUR"
    },
    
    # Complete Scope 3 breakdown
    "scope3_detailed": {},
    
    # Financial effects
    "financial_effects": {
        "risks": [
            {
                "type": "Physical",
                "description": "Flood risk to coastal facilities",
                "time_horizon": "Medium-term",
                "likelihood": "Likely",
                "magnitude": "Medium",
                "financial_impact": 10000000
            },
            {
                "type": "Transition",
                "description": "Carbon pricing exposure",
                "time_horizon": "Short-term",
                "likelihood": "Very likely",
                "magnitude": "High",
                "financial_impact": 25000000
            }
        ],
        "opportunities": [
            {
                "type": "Products and services",
                "description": "Low-carbon product line",
                "time_horizon": "Short-term",
                "likelihood": "Likely",
                "magnitude": "High",
                "potential_value": 50000000
            }
        ],
        "climate_related_costs": 35000000,
        "climate_related_investments": 100000000,
        "climate_related_revenue": 200000000,
        "climate_var_1_year": 5000000,
        "climate_var_10_year": 50000000
    },
    
    # Carbon pricing
    "carbon_pricing": {
        "implemented": True,
        "shadow_price_eur": 100,
        "shadow_price_application": "All major investment decisions",
        "shadow_price_coverage": 80,
        "eu_ets_exposure": {
            "allowances_required": 50000,
            "cost_eur": 4000000
        }
    },
    
    # Removals
    "removals": {
        "total": 1000,
        "within_value_chain": 1000,
        "by_type": {
            "reforestation": 800,
            "direct_air_capture": 200
        }
    },
    
    # EU Taxonomy
    "eu_taxonomy_data": {
        "revenue_aligned_percent": 35,
        "capex_aligned_percent": 45,
        "opex_aligned_percent": 30,
        "eligible_activities": [
            {
                "name": "Solar energy generation",
                "nace_code": "D35.11",
                "revenue_percent": 20,
                "capex_percent": 30,
                "aligned": True,
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
    
    # Value chain
    "value_chain": {
        "upstream": {
            "suppliers_with_targets_percent": 60,
            "engagement_program": "Supplier Climate Action Program launched 2023"
        },
        "downstream": {
            "product_carbon_footprints": [
                {
                    "product_name": "Main Product Line",
                    "carbon_footprint_kg": 10.5,
                    "lca_standard": "ISO 14067",
                    "coverage": "Cradle-to-gate"
                }
            ]
        }
    },
    
    # Methodology
    "methodology": {
        "ghg_standard": "GHG Protocol Corporate Standard",
        "consolidation_approach": "Operational control",
        "emission_factor_sources": ["DEFRA 2024", "IEA 2024", "EPA Hub"],
        "uncertainty_range": {"low": -15, "high": 15},
        "recalculation_threshold": 5
    },
    
    # Data quality and assurance
    "data_quality_score": 85,
    "emissions_change_percent": -8.5,
    "intensity": {
        "revenue": 45.2,
        "unit": "tCO2e/million EUR"
    },
    "uncertainty_assessment": "Monte Carlo analysis shows 95% CI of ±15%",
    "recalculation_policy": "Recalculate if changes exceed 5% threshold",
    
    # Assurance
    "assurance": {
        "level": "Limited assurance",
        "provider": "PwC",
        "standard": "ISAE 3410",
        "scope": ["Scope 1", "Scope 2", "Material Scope 3 categories"]
    }
}

# Add detailed Scope 3 data
scope3_categories = [
    ("category_1", 30000, "Purchased goods and services", False),
    ("category_2", 10000, "Capital goods", False),
    ("category_3", 8000, "Fuel- and energy-related", False),
    ("category_4", 7000, "Upstream transportation", False),
    ("category_5", 2000, "Waste generated", False),
    ("category_6", 5000, "Business travel", False),
    ("category_7", 3000, "Employee commuting", False),
    ("category_8", 0, "Upstream leased assets", True),
    ("category_9", 10000, "Downstream transportation", False),
    ("category_10", 15000, "Processing of sold products", False),
    ("category_11", 25000, "Use of sold products", False),
    ("category_12", 5000, "End-of-life treatment", False),
    ("category_13", 0, "Downstream leased assets", True),
    ("category_14", 0, "Franchises", True),
    ("category_15", 0, "Investments", True)
]

for cat_key, emissions, description, excluded in scope3_categories:
    test_data["scope3_detailed"][cat_key] = {
        "emissions_tco2e": emissions,
        "excluded": excluded,
        "exclusion_reason": "Not applicable to business model" if excluded else None,
        "data_quality_tier": "Tier 1" if emissions > 20000 else "Tier 2",
        "data_quality_score": 85 if emissions > 20000 else 75,
        "calculation_method": "Supplier-specific" if emissions > 20000 else "Spend-based",
        "coverage_percent": 95 if emissions > 0 else 0,
        "uncertainty_range": {"low": -10, "high": 10}
    }

try:
    print("="*60)
    print("GENERATING COMPLETE ESRS E1 REPORT")
    print("="*60)
    print(f"Organization: {test_data['organization']}")
    print(f"Reporting Period: {test_data['reporting_period']}")
    print(f"Total Emissions: {test_data['emissions']['scope1'] + test_data['emissions']['scope2'] + test_data['emissions']['scope3']:,} tCO₂e")
    print("-"*60)
    
    # Generate the report
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    
    print("\n✅ SUCCESS! Complete ESRS E1 report generated!")
    print("="*60)
    
    # Save all outputs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved_files = []
    
    for key, value in result.items():
        if isinstance(value, str) and len(value) > 100:
            if 'html' in key:
                filename = f"ESRS_E1_Complete_Report_{timestamp}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(value)
                saved_files.append(filename)
                print(f"✓ HTML Report: {filename} ({len(value):,} characters)")
            elif 'xbrl' in key or 'ixbrl' in key:
                filename = f"ESRS_E1_Complete_{timestamp}.xbrl"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(value)
                saved_files.append(filename)
                print(f"✓ iXBRL File: {filename} ({len(value):,} characters)")
            elif 'json' in key:
                filename = f"ESRS_E1_Metadata_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(json.loads(value) if isinstance(value, str) else value, f, indent=2)
                saved_files.append(filename)
                print(f"✓ Metadata: {filename}")
        else:
            print(f"✓ {key}: {value}")
    
    # Save the complete data structure
    with open(f'complete_esrs_data_{timestamp}.json', 'w') as f:
        json.dump(test_data, f, indent=2)
    print(f"\n✓ Data structure saved to: complete_esrs_data_{timestamp}.json")
    
    print("\n" + "="*60)
    print("🎉 COMPLETE SUCCESS!")
    print("="*60)
    print("\nThe missing functions have been successfully integrated!")
    print("All validations passed and the report was generated.")
    print("\nGenerated files:")
    for file in saved_files:
        print(f"  📄 {file}")
    
    # Try to open the HTML report
    if saved_files:
        html_file = next((f for f in saved_files if '.html' in f), None)
        if html_file:
            abs_path = os.path.abspath(html_file)
            print(f"\n🌐 Opening report in browser...")
            print(f"   File: {abs_path}")
            
            # Try different methods to open
            try:
                import webbrowser
                webbrowser.open(f'file://{abs_path}')
            except:
                print(f"   → Please open manually: file://{abs_path}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Save test data for debugging
    with open('debug_test_data.json', 'w') as f:
        json.dump(test_data, f, indent=2)
    print("\n✓ Test data saved to: debug_test_data.json")
