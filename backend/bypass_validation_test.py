#!/usr/bin/env python3
"""
Test iXBRL generation by bypassing validation
"""

import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔧 Testing iXBRL generation with validation bypass")
print("="*50)

# First, let's check the actual validation
print("\n1️⃣ Checking validation code...")
with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
    content = f.read()

# Find the validation that's blocking us
validation_line = None
for i, line in enumerate(content.split('\n')):
    if "Valid LEI required for ESAP submission" in line:
        validation_line = i + 1
        print(f"Found validation error at line {validation_line}")
        
        # Show surrounding context
        lines = content.split('\n')
        start = max(0, i - 10)
        end = min(len(lines), i + 5)
        
        print("\nContext:")
        for j in range(start, end):
            marker = ">>>" if j == i else "   "
            print(f"{marker} {j+1}: {lines[j]}")

# Create a patched version that bypasses validation
print("\n2️⃣ Creating patched version...")

# Make a temporary copy
import shutil
shutil.copy("app/api/v1/endpoints/esrs_e1_full.py", "app/api/v1/endpoints/esrs_e1_full_original.py")

# Create patched content
patched_content = content

# Method 1: Try to bypass the validation check
if "blocking_issues.append" in content and "Valid LEI required" in content:
    # Comment out the LEI validation
    patched_content = re.sub(
        r'(blocking_issues\.append\(["\']Valid LEI required[^)]*\))',
        r'# BYPASSED: \1',
        patched_content
    )
    print("✅ Commented out LEI validation")

# Method 2: Set a flag to skip validation
if "validate_" in content or "validation" in content:
    # Add bypass at the beginning of generate function
    patched_content = re.sub(
        r'(def generate_world_class_esrs_e1_ixbrl\([^)]*\):[^\n]*\n)',
        r'\1    # BYPASS VALIDATION FOR TESTING\n    bypass_validation = True\n',
        patched_content
    )
    
    # Use the bypass flag
    patched_content = re.sub(
        r'if\s+blocking_issues:',
        r'if blocking_issues and not bypass_validation:',
        patched_content
    )
    print("✅ Added validation bypass flag")

# Save patched version
with open("app/api/v1/endpoints/esrs_e1_full.py", "w") as f:
    f.write(patched_content)

print("\n3️⃣ Testing with patched version...")

# Now try to import and run
try:
    # Force reload the module
    if 'app.api.v1.endpoints.esrs_e1_full' in sys.modules:
        del sys.modules['app.api.v1.endpoints.esrs_e1_full']
    
    from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl
    
    # Test data
    test_data = {
        "entity": {
            "name": "Test Company Ltd",
            "lei": "ABCDEFGHIJ1234567890",
            "lei_code": "ABCDEFGHIJ1234567890",  # Try both fields
            "identifier_scheme": "http://standards.iso.org/iso/17442",
            "sector": "Technology",
            "primary_nace_code": "62.01",
            "consolidation_scope": "consolidated"
        },
        "period": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "reporting_year": 2024
        },
        "climate_change": {
            "ghg_emissions": {
                "scope1_total": 1500,
                "scope2_location": 800,
                "scope2_market": 600,
                "scope3_total": 5000,
                "total_ghg_emissions": 7300
            }
        }
    }
    
    # Try to generate
    print("\n4️⃣ Generating report...")
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    
    # Check result
    if isinstance(result, dict):
        xhtml_content = result.get("content", result.get("xhtml_content", ""))
        filename = result.get("filename", "bypass_test.xhtml")
        
        if xhtml_content:
            # Save it
            with open(filename, "w") as f:
                f.write(xhtml_content)
            
            print(f"✅ Generated: {filename}")
            
            # Check for iXBRL tags
            fractions = len(re.findall(r'<ix:nonFraction', xhtml_content))
            numerics = len(re.findall(r'<ix:nonNumeric', xhtml_content))
            
            print(f"\n📊 iXBRL tags found:")
            print(f"   ix:nonFraction: {fractions}")
            print(f"   ix:nonNumeric: {numerics}")
            
            if fractions > 0 or numerics > 0:
                print("\n✅ SUCCESS! iXBRL generation works!")
                print(f"The issue was only the validation!")
            else:
                print("\n❌ Still no iXBRL tags - the issue is in tag generation")
                
                # Check if create_enhanced_xbrl_tag is being called
                if 'create_enhanced_xbrl_tag' in xhtml_content:
                    print("⚠️  Found 'create_enhanced_xbrl_tag' in output - function not processed!")
                
                # Save a sample for debugging
                with open("bypass_debug.html", "w") as f:
                    f.write(xhtml_content[:5000])
                print("Saved first 5000 chars to bypass_debug.html")
        else:
            print("❌ No content generated")
    else:
        print(f"❌ Unexpected result type: {type(result)}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Restore original file
    print("\n5️⃣ Restoring original file...")
    if os.path.exists("app/api/v1/endpoints/esrs_e1_full_original.py"):
        shutil.move("app/api/v1/endpoints/esrs_e1_full_original.py", "app/api/v1/endpoints/esrs_e1_full.py")
        print("✅ Original file restored")