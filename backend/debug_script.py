#!/usr/bin/env python3
"""
Quick debugging script to trace where Scope 3 emissions data is being lost
"""

import json
import requests
from datetime import datetime

def debug_esrs_endpoint():
    """Test the endpoint and trace data flow"""
    
    # Test data with clear values
    test_data = {
        "company_name": "Debug Test Corp",
        "lei": "12345678901234567890",  # Valid 20-char LEI
        "reporting_period": "2024",
        "organization": "Debug Test Corp",
        "force_generation": True,
        "emissions": {
            "scope1": 1111,      # Easy to spot
            "scope2_location": 2222,
            "scope3": 3333,      # This is getting lost!
            "total": 6666
        }
    }
    
    print("=" * 60)
    print("ESRS E1 Generator Debug Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print("\n1. INPUT DATA:")
    print(json.dumps(test_data, indent=2))
    
    # Make the request
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/esrs-e1/export/esrs-e1-world-class",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n2. RESPONSE STATUS: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if response has expected structure
            if 'xhtml_content' in result:
                xhtml = result['xhtml_content']
                
                print("\n3. CHECKING OUTPUT FOR KEY VALUES:")
                
                # Search for our test values in the output
                checks = [
                    ("Scope 1 (1111)", "1111", "✓ Found" if "1111" in xhtml else "✗ MISSING"),
                    ("Scope 2 (2222)", "2222", "✓ Found" if "2222" in xhtml else "✗ MISSING"),
                    ("Scope 3 (3333)", "3333", "✓ Found" if "3333" in xhtml else "✗ MISSING"),
                    ("Total (6666)", "6666", "✓ Found" if "6666" in xhtml else "✗ MISSING"),
                ]
                
                for name, value, status in checks:
                    print(f"  {name}: {status}")
                    if "MISSING" in status and value in ["3333", "6666"]:
                        # Look for what value is actually there
                        import re
                        pattern = rf'GrossScope3Emissions[^>]*>(\d+)<'
                        match = re.search(pattern, xhtml)
                        if match:
                            print(f"    → Found Scope3 value: {match.group(1)} instead")
                
                # Check for calculation issues
                print("\n4. CHECKING CALCULATIONS:")
                
                # Extract actual values from output
                import re
                scope1_match = re.search(r'GrossScope1Emissions[^>]*>(\d+)<', xhtml)
                scope2_match = re.search(r'GrossScope2LocationBased[^>]*>(\d+)<', xhtml)
                scope3_match = re.search(r'GrossScope3Emissions[^>]*>(\d+)<', xhtml)
                total_match = re.search(r'TotalGHGEmissions[^>]*>(\d+)<', xhtml)
                
                if all([scope1_match, scope2_match, scope3_match, total_match]):
                    actual_scope1 = int(scope1_match.group(1))
                    actual_scope2 = int(scope2_match.group(1))
                    actual_scope3 = int(scope3_match.group(1))
                    actual_total = int(total_match.group(1))
                    calculated = actual_scope1 + actual_scope2 + actual_scope3
                    
                    print(f"  Output Scope 1: {actual_scope1}")
                    print(f"  Output Scope 2: {actual_scope2}")
                    print(f"  Output Scope 3: {actual_scope3}")
                    print(f"  Output Total: {actual_total}")
                    print(f"  Calculated Total: {calculated}")
                    print(f"  Match: {'✓' if calculated == actual_total else '✗'}")
                
                # Check namespace issues
                print("\n5. NAMESPACE CHECKS:")
                if "ns0:nonFraction" in xhtml:
                    print("  ✗ Using 'ns0:' prefix (should be 'ix:')")
                elif "ix:nonFraction" in xhtml:
                    print("  ✓ Using correct 'ix:' prefix")
                else:
                    print("  ? No inline XBRL facts found")
                
                # Save output for inspection
                filename = f"debug_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(filename, 'w') as f:
                    f.write(xhtml)
                print(f"\n6. OUTPUT SAVED TO: {filename}")
                
            else:
                print("\n✗ ERROR: No 'xhtml_content' in response")
                print("Response keys:", list(result.keys()))
        
        else:
            print(f"\n✗ ERROR: Request failed")
            print("Response:", response.text)
            
    except Exception as e:
        print(f"\n✗ EXCEPTION: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print("=" * 60)
    print("If Scope 3 shows as 0 instead of 3333, check:")
    print("1. Is the 'scope3' field being read from input JSON?")
    print("2. Is it being passed to the emissions data structure?")
    print("3. Is the XBRL fact being created with the correct value?")
    print("4. Are there any default values overwriting it?")
    print("\nLook for code like:")
    print("  scope3 = emissions.get('scope3', 0)  # This might be the issue")
    print("  scope3 = 0  # Or hardcoded to 0")
    print("=" * 60)

if __name__ == "__main__":
    debug_esrs_endpoint()