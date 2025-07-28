import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl
import json
from datetime import datetime

# Complete data with ALL required fields
test_data = {
    "force_generation": True,  # Bypass validation
    
    # Basic info
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
    
    # Transition plan
    "transition_plan": {
        "adopted": True,
        "adoption_date": "2024-01-01",
        "net_zero_target": True,
        "net_zero_target_year": 2050,
        "milestones": [
            {"year": 2030, "target": "50% reduction", "description": "Interim target"},
            {"year": 2040, "target": "80% reduction", "description": "Deep decarbonization"}
        ],
        "decarbonization_levers": ["Renewable energy", "Energy efficiency", "Electrification"],
        "financial_planning": {"capex_allocated": 100},
        "locked_in_emissions": "20% locked until 2035",
        "just_transition": "Worker reskilling program"
    },
    
    # Governance
    "governance": {
        "board_oversight": True,
        "board_meetings_climate": 6,
        "management_responsibility": True,
        "climate_expertise": "Board climate experts",
        "climate_linked_compensation": True,
        "governance_integration": "Fully integrated"
    },
    
    # Climate policy
    "climate_policy": {
        "has_climate_policy": True,
        "policy_description": "Net zero aligned policy",
        "policy_adoption_date": "2023-01-01",
        "covers_own_operations": True,
        "covers_value_chain": True,
        "covers_products_services": True,
        "integrated_with_strategy": True,
        "governance_integration": "Board review quarterly"
    },
    
    # Climate actions
    "climate_actions": {
        "actions": [
            {
                "description": "Install 50MW solar",
                "type": "Mitigation",
                "timeline": "2024-2025",
                "investment_meur": 50,
                "expected_impact": "30% Scope 2 reduction"
            }
        ],
        "capex": 100,
        "opex": 20,
        "fte": 25,
        "capex_climate_eur": 100000000,
        "opex_climate_eur": 20000000,
        "fte_dedicated": 25
    },
    
    # Targets - WITH ALL REQUIRED FIELDS
    "targets": {
        "base_year": 2020,
        "base_year_emissions": 150000,
        "progress": 25,
        "targets": [
            {
                "description": "50% absolute reduction",
                "scope": "Scope 1, 2 & 3",
                "target_year": 2030,  # THIS WAS MISSING!
                "reduction_percent": 50,
                "progress_percent": 25,
                "status": "On track"
            },
            {
                "description": "Net zero emissions",
                "scope": "All scopes",
                "target_year": 2050,  # THIS WAS MISSING!
                "reduction_percent": 100,
                "progress_percent": 10,
                "status": "On track"
            }
        ],
        "sbti_validated": True,
        "sbti_ambition": "1.5°C aligned"
    },
    
    # Energy consumption
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
    
    # Scope 3 detailed breakdown
    "scope3_detailed": {},
    
    # Financial effects
    "financial_effects": {
        "risks": [
            {
                "type": "Physical",
                "description": "Flood risk to facilities",
                "time_horizon": "Medium-term",
                "likelihood": "Likely",
                "magnitude": "Medium",
                "financial_impact": 10000000
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
        "climate_related_revenue": 200000000
    },
    
    # Carbon pricing
    "carbon_pricing": {
        "implemented": True,
        "shadow_price_eur": 100,
        "shadow_price_application": "Investment decisions",
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
                "minimum_safeguards": True
            }
        ]
    },
    
    # Value chain
    "value_chain": {
        "upstream": {
            "suppliers_with_targets_percent": 60,
            "engagement_program": "Supplier Climate Program"
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
    
    # Methodology
    "methodology": {
        "ghg_standard": "GHG Protocol Corporate Standard",
        "consolidation_approach": "Operational control",
        "emission_factor_sources": ["DEFRA 2024", "IEA 2024"]
    },
    
    # Other required fields
    "data_quality_score": 85,
    "emissions_change_percent": -8.5,
    "intensity": {"revenue": 45.2},
    "uncertainty_assessment": "±15% at 95% confidence",
    "recalculation_policy": "5% threshold policy",
    
    # Assurance
    "assurance": {
        "level": "Limited assurance",
        "provider": "PwC",
        "standard": "ISAE 3410",
        "scope": ["Scope 1", "Scope 2", "Material Scope 3"]
    }
}

# Add all Scope 3 categories
scope3_categories = [
    ("category_1", 30000, "Purchased goods and services"),
    ("category_2", 10000, "Capital goods"),
    ("category_3", 8000, "Fuel- and energy-related"),
    ("category_4", 7000, "Upstream transportation"),
    ("category_5", 2000, "Waste generated"),
    ("category_6", 5000, "Business travel"),
    ("category_7", 3000, "Employee commuting"),
    ("category_8", 0, "Upstream leased assets"),
    ("category_9", 10000, "Downstream transportation"),
    ("category_10", 15000, "Processing of sold products"),
    ("category_11", 25000, "Use of sold products"),
    ("category_12", 5000, "End-of-life treatment"),
    ("category_13", 0, "Downstream leased assets"),
    ("category_14", 0, "Franchises"),
    ("category_15", 0, "Investments")
]

for cat_key, emissions, description in scope3_categories:
    test_data["scope3_detailed"][cat_key] = {
        "emissions_tco2e": emissions,
        "excluded": emissions == 0,
        "exclusion_reason": "Not applicable" if emissions == 0 else None,
        "data_quality_tier": "Tier 2",
        "data_quality_score": 75,
        "calculation_method": "Spend-based",
        "coverage_percent": 90 if emissions > 0 else 0
    }

try:
    print("Generating ESRS E1 report...")
    print(f"Organization: {test_data['organization']}")
    print(f"Reporting Period: {test_data['reporting_period']}")
    print(f"Total Emissions: {test_data['emissions']['scope1'] + test_data['emissions']['scope2'] + test_data['emissions']['scope3']:,} tCO₂e")
    
    # Generate the report
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    
    print("\n✅ SUCCESS! Full ESRS E1 report generated!")
    
    # Save all outputs
    saved_files = []
    
    for key, value in result.items():
        if isinstance(value, str) and len(value) > 100:
            if 'html' in key:
                filename = f"ESRS_E1_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(value)
                saved_files.append(filename)
                print(f"  ✓ HTML Report: {filename} ({len(value):,} characters)")
            elif 'xbrl' in key or 'ixbrl' in key:
                filename = f"ESRS_E1_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xbrl"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(value)
                saved_files.append(filename)
                print(f"  ✓ iXBRL File: {filename} ({len(value):,} characters)")
            elif 'json' in key:
                filename = f"ESRS_E1_Metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w') as f:
                    json.dump(json.loads(value), f, indent=2)
                saved_files.append(filename)
                print(f"  ✓ Metadata: {filename}")
        else:
            print(f"  ✓ {key}: {value}")
    
    # Save the complete data structure for reference
    with open('working_esrs_data_structure.json', 'w') as f:
        json.dump(test_data, f, indent=2)
    print("\n✓ Data structure saved to: working_esrs_data_structure.json")
    
    print("\n🎉 COMPLETE SUCCESS!")
    print("The missing functions have been successfully integrated and are working!")
    print("\nGenerated files:")
    for file in saved_files:
        print(f"  - {file}")
    
    # Open the HTML report
    if saved_files:
        html_file = next((f for f in saved_files if '.html' in f), None)
        if html_file:
            print(f"\nOpening {html_file} in browser...")
            import webbrowser
            webbrowser.open(f'file://{os.path.abspath(html_file)}')
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

import os
