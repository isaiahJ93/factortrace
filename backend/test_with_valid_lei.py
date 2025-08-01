#!/usr/bin/env python3
"""
Test ESRS endpoint with valid LEI and complete data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trying alternative import...")
    import importlib.util
    spec = importlib.util.spec_from_file_location("esrs_e1_full", "app/api/v1/endpoints/esrs_e1_full.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    generate_world_class_esrs_e1_ixbrl = module.generate_world_class_esrs_e1_ixbrl

from datetime import datetime
import re

# Test data with VALID LEI (20 uppercase alphanumeric characters)
test_data = {
    "entity": {
        "name": "Test Company Ltd",
        "lei": "ABCDEFGHIJ1234567890",  # Valid format LEI
        "identifier_scheme": "http://standards.iso.org/iso/17442",
        "sector": "Technology",
        "primary_nace_code": "62.01",
        "consolidation_scope": "consolidated",
        "reporting_boundary": "financial_control"
    },
    "period": {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "reporting_year": 2024,
        "comparative_year": 2023
    },
    "climate_change": {
        "transition_plan": {
            "has_transition_plan": True,
            "aligned_1_5c": True,
            "net_zero_target_year": 2050,
            "science_based_targets": True,
            "transition_plan_disclosure": "We have committed to net-zero by 2050"
        },
        "targets": {
            "absolute_targets": [{
                "base_year": 2023,
                "target_year": 2030,
                "target_reduction_percent": 50,
                "scopes_covered": ["scope1", "scope2", "scope3"]
            }],
            "intensity_targets": []
        },
        "ghg_emissions": {
            "scope1_total": 1500.5,
            "scope1_breakdown": {
                "stationary_combustion": 900.3,
                "mobile_combustion": 450.15,
                "process_emissions": 75.025,
                "fugitive_emissions": 75.025
            },
            "scope2_location": 800.0,
            "scope2_market": 600.0,
            "scope3_total": 5000.0,
            "scope3_categories": {
                "cat1_purchased_goods": 1250.0,
                "cat2_capital_goods": 250.0,
                "cat3_fuel_energy": 500.0,
                "cat4_upstream_transport": 400.0,
                "cat5_waste": 100.0,
                "cat6_business_travel": 150.0,
                "cat7_employee_commuting": 100.0,
                "cat8_upstream_leased": 50.0,
                "cat9_downstream_transport": 450.0,
                "cat10_processing_sold": 250.0,
                "cat11_use_of_sold": 1250.0,
                "cat12_end_of_life": 150.0,
                "cat13_downstream_leased": 50.0,
                "cat14_franchises": 0.0,
                "cat15_investments": 50.0
            },
            "total_ghg_emissions": 7300.5,
            "ghg_breakdown": {
                "co2_fossil": 6716.46,
                "co2_biogenic": 219.015,
                "ch4": 219.015,
                "n2o": 146.01,
                "hfcs": 0,
                "pfcs": 0,
                "sf6": 0,
                "nf3": 0
            },
            "intensity_metrics": {
                "per_revenue": 0.00073,
                "per_employee": 73.005
            }
        },
        "carbon_removals": {
            "total_removals": 0,
            "removal_projects": []
        },
        "carbon_pricing": {
            "exposed_to_ets": False,
            "total_emissions_under_ets": 0,
            "carbon_credits_purchased": 0
        }
    },
    "data_quality": {
        "estimation_methods_used": True,
        "third_party_verified": False,
        "verification_standard": None,
        "data_gaps_disclosed": True,
        "completeness_score": 85.0,  # Add completeness score
        "data_sources": ["Primary data", "Emission factors"]
    },
    "metadata": {
        "report_type": "ESRS_E1_CLIMATE_CHANGE",
        "taxonomy_version": "EFRAG_ESRS_2023",
        "creation_timestamp": datetime.now().isoformat(),
        "preparer_name": "Sustainability Team",
        "preparer_email": "sustainability@testcompany.com",
        "language": "en",
        "currency": "EUR"
    }
}

def test_ixbrl_generation():
    print("🧪 Testing iXBRL generation with valid LEI...")
    
    try:
        
        # Generate the report
        print("\n2️⃣ Generating ESRS E1 report...")
        result = generate_world_class_esrs_e1_ixbrl(test_data)
        
        # Extract XHTML content
        xhtml_content = result.get("content", result.get("xhtml_content", ""))
        filename = result.get("filename", "esrs_fixed_output.xhtml")
        
        if xhtml_content:
            # Save to file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(xhtml_content)
            
            print(f"✅ Generated: {filename}")
            
            # Validation
            print("\n🔍 Validating iXBRL content...")
            
            # Check for iXBRL tags
            has_nonfraction = '<ix:nonFraction' in xhtml_content
            has_nonnumeric = '<ix:nonNumeric' in xhtml_content
            has_contextref = 'contextRef=' in xhtml_content
            has_unitref = 'unitRef=' in xhtml_content
            has_values = re.search(r'<ix:nonFraction[^>]*>[\d,\.]+</ix:nonFraction>', xhtml_content) is not None
            
            print(f"✅ Contains ix:nonFraction tags: {has_nonfraction}")
            print(f"✅ Contains ix:nonNumeric tags: {has_nonnumeric}")
            print(f"✅ Contains contextRef attributes: {has_contextref}")
            print(f"✅ Contains unitRef attributes: {has_unitref}")
            print(f"✅ Tags contain actual values: {has_values}")
            
            # Count facts
            fractions = len(re.findall(r'<ix:nonFraction', xhtml_content))
            numerics = len(re.findall(r'<ix:nonNumeric', xhtml_content))
            
            print(f"\n📊 Fact counts:")
            print(f"  Numeric facts: {fractions}")
            print(f"  Text facts: {numerics}")
            print(f"  Total facts: {fractions + numerics}")
            
            # Check for specific values
            if has_values:
                print("\n🔍 Sample tagged values:")
                # Find first few numeric values
                numeric_matches = re.findall(r'<ix:nonFraction[^>]*name="([^"]*)"[^>]*>([^<]+)</ix:nonFraction>', xhtml_content)[:5]
                for name, value in numeric_matches:
                    print(f"  - {name}: {value}")
                
                # Find first few text values
                text_matches = re.findall(r'<ix:nonNumeric[^>]*name="([^"]*)"[^>]*>([^<]+)</ix:nonNumeric>', xhtml_content)[:3]
                for name, value in text_matches:
                    print(f"  - {name}: {value[:50]}...")
            
            # Check namespaces
            if 'xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"' in xhtml_content:
                print("\n✅ Has proper ix namespace declaration")
            
            # Final verdict
            is_valid = has_nonfraction and has_nonnumeric and has_values and fractions > 0
            print(f"\n{'✅' if is_valid else '❌'} iXBRL Generation: {'SUCCESSFUL' if is_valid else 'FAILED'}")
            
            if is_valid:
                print(f"\n🎉 Success! Run this to verify:")
                print(f"   python3 verify_ixbrl.py {filename}")
            else:
                print("\n❌ Still missing proper iXBRL tags")
                print("Debug: Check if create_enhanced_xbrl_tag is being called correctly")
                
                # Save first 5000 chars for inspection
                with open("debug_output.html", "w") as f:
                    f.write(xhtml_content[:5000])
                print("Saved first 5000 chars to debug_output.html")
                
        else:
            print("❌ No content generated")
            print("Result keys:", list(result.keys()))
            if "error" in result:
                print("Error:", result["error"])
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ixbrl_generation()