#!/usr/bin/env python3
"""
Test the fixed ESRS E1 endpoint
"""

import requests
import json
from datetime import datetime

# Test data matching your frontend structure
test_data = {
    "entity": {
        "name": "Test Company Ltd",
        "lei": "12345678901234567890",
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
            "science_based_targets": True
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
        "data_gaps_disclosed": True
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

def test_local_endpoint():
    """Test the local endpoint"""
    url = "http://localhost:8000/api/v1/esrs-e1/export/esrs-e1-world-class"
    
    print(f"🚀 Testing endpoint: {url}")
    print("📊 Sending test data...")
    
    try:
        response = requests.post(url, json=test_data)
        
        print(f"\n📬 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract the XHTML content
            xhtml_content = result.get("content", result.get("xhtml_content", ""))
            filename = result.get("filename", "esrs_test_output.xhtml")
            
            if xhtml_content:
                # Save to file
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(xhtml_content)
                
                print(f"✅ Saved output to: {filename}")
                
                # Quick validation
                print("\n🔍 Quick Validation:")
                if '<ix:nonFraction' in xhtml_content:
                    print("✅ Contains ix:nonFraction tags")
                else:
                    print("❌ Missing ix:nonFraction tags")
                
                if '<ix:nonNumeric' in xhtml_content:
                    print("✅ Contains ix:nonNumeric tags") 
                else:
                    print("❌ Missing ix:nonNumeric tags")
                
                if 'contextRef=' in xhtml_content:
                    print("✅ Contains contextRef attributes")
                else:
                    print("❌ Missing contextRef attributes")
                    
                # Count facts
                import re
                fractions = len(re.findall(r'<ix:nonFraction', xhtml_content))
                numerics = len(re.findall(r'<ix:nonNumeric', xhtml_content))
                
                print(f"\n📊 Fact counts:")
                print(f"  Numeric facts: {fractions}")
                print(f"  Text facts: {numerics}")
                
                print(f"\n✅ Now run: python3 verify_ixbrl.py {filename}")
                
            else:
                print("❌ No XHTML content in response")
                print("Response keys:", list(result.keys()))
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure FastAPI is running on port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_direct_import():
    """Test by importing the function directly"""
    print("\n🧪 Testing direct import...")
    
    try:
        from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl
        
        result = generate_world_class_esrs_e1_ixbrl(test_data)
        
        xhtml_content = result.get("content", "")
        filename = "esrs_direct_test.xhtml"
        
        if xhtml_content:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(xhtml_content)
            
            print(f"✅ Generated {filename} via direct import")
            
            # Validate
            if '<ix:nonFraction' in xhtml_content:
                print("✅ Contains iXBRL tags!")
            else:
                print("❌ Still missing iXBRL tags")
                
    except Exception as e:
        print(f"❌ Direct import failed: {e}")

if __name__ == "__main__":
    # First apply the fix
    print("🔧 Applying fixes to esrs_e1_full.py...")
    import subprocess
    subprocess.run(["python3", "direct_fix_esrs_e1.py"])
    
    print("\n" + "="*50)
    
    # Test via endpoint
    test_local_endpoint()
    
    # Test via direct import
    test_direct_import()