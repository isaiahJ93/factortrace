#!/usr/bin/env python3
"""
Direct test of create_enhanced_xbrl_tag without going through full validation
"""

import xml.etree.ElementTree as ET
import sys
import os

print("🧪 Direct test of iXBRL tag creation")
print("="*50)

# Register namespaces
ET.register_namespace('', 'http://www.w3.org/1999/xhtml')
ET.register_namespace('ix', 'http://www.xbrl.org/2013/inlineXBRL')
ET.register_namespace('xbrli', 'http://www.xbrl.org/2003/instance')

# Import the function
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import create_enhanced_xbrl_tag
    from app.api.v1.endpoints.esrs_e1_full import create_enhanced_xbrl_tag
    print("✅ Imported create_enhanced_xbrl_tag")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    # Try to extract and use the function directly
    print("\nExtracting function from file...")
    
    with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
        content = f.read()
    
    # Find the latest definition
    import re
    matches = list(re.finditer(r'def create_enhanced_xbrl_tag\s*\([^}]+\}(?=\n\ndef|\nclass|\Z)', content, re.DOTALL))
    
    if not matches:
        print("❌ Could not find function!")
        exit(1)
    
    # Use the last definition
    func_code = matches[-1].group(0)
    print(f"Found function ({len(func_code)} chars)")
    
    # Create execution environment
    exec_globals = {
        'ET': ET,
        'Any': object,
        'Optional': lambda x: x,
        'str': str,
        'int': int,
        'float': float,
        '__builtins__': __builtins__
    }
    
    # Execute the function
    exec(func_code, exec_globals)
    create_enhanced_xbrl_tag = exec_globals['create_enhanced_xbrl_tag']

# Test the function directly
print("\n1️⃣ Testing create_enhanced_xbrl_tag directly...")

# Create a simple HTML structure
root = ET.Element('{http://www.w3.org/1999/xhtml}html')
root.set('{http://www.w3.org/2000/xmlns/}ix', 'http://www.xbrl.org/2013/inlineXBRL')
root.set('{http://www.w3.org/2000/xmlns/}xbrli', 'http://www.xbrl.org/2003/instance')

body = ET.SubElement(root, '{http://www.w3.org/1999/xhtml}body')
div = ET.SubElement(body, '{http://www.w3.org/1999/xhtml}div')

# Test numeric fact
print("\n   Testing numeric fact...")
p1 = ET.SubElement(div, '{http://www.w3.org/1999/xhtml}p')
p1.text = "Scope 1 emissions: "

try:
    elem1 = create_enhanced_xbrl_tag(
        parent=p1,
        tag_type='nonFraction',
        name='esrs:Scope1Emissions',
        context_ref='c1',
        value=1500.5,
        unit_ref='tCO2e',
        decimals='1'
    )
    
    # Check what was created
    elem1_str = ET.tostring(elem1, encoding='unicode') if elem1 is not None else "None"
    print(f"   Created: {elem1_str}")
    
    if '<ix:nonFraction' in elem1_str or '<ns0:nonFraction' in elem1_str:
        print("   ✅ Numeric fact created successfully!")
    else:
        print("   ❌ Wrong element type created")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test text fact
print("\n   Testing text fact...")
p2 = ET.SubElement(div, '{http://www.w3.org/1999/xhtml}p')
p2.text = "Company: "

try:
    elem2 = create_enhanced_xbrl_tag(
        parent=p2,
        tag_type='nonNumeric',
        name='esrs:EntityName',
        context_ref='c1',
        value='Test Company & Co',
        xml_lang='en'
    )
    
    elem2_str = ET.tostring(elem2, encoding='unicode') if elem2 is not None else "None"
    print(f"   Created: {elem2_str}")
    
    if '<ix:nonNumeric' in elem2_str or '<ns0:nonNumeric' in elem2_str:
        print("   ✅ Text fact created successfully!")
    else:
        print("   ❌ Wrong element type created")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Convert the whole structure to string
print("\n2️⃣ Full document test...")
full_xml = ET.tostring(root, encoding='unicode')

# Save it
with open('direct_test.xhtml', 'w') as f:
    f.write('<!DOCTYPE html>\n' + full_xml)

print("✅ Saved to direct_test.xhtml")

# Check content
import re
fractions = len(re.findall(r'<(?:ix:|ns\d+:)nonFraction', full_xml))
numerics = len(re.findall(r'<(?:ix:|ns\d+:)nonNumeric', full_xml))

print(f"\n📊 Results:")
print(f"   Numeric facts: {fractions}")
print(f"   Text facts: {numerics}")

if fractions > 0 and numerics > 0:
    print("\n✅ SUCCESS! The function works correctly!")
    print("The issue must be elsewhere in the code.")
else:
    print("\n❌ Function is not creating proper iXBRL elements")
    
    # Debug info
    print("\n🔍 Debug info:")
    print(f"   Full XML preview (first 500 chars):")
    print(full_xml[:500])