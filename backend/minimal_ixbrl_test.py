#!/usr/bin/env python3
"""
Minimal test to ensure iXBRL generation works
"""

import xml.etree.ElementTree as ET
from typing import Any, Optional

# First, let's define a WORKING create_enhanced_xbrl_tag function
def create_enhanced_xbrl_tag(
    parent: ET.Element,
    tag_type: str,
    name: str,
    context_ref: str,
    value: Any,
    unit_ref: str = None,
    decimals: str = None,
    xml_lang: str = None,
    **kwargs
) -> ET.Element:
    """Create proper iXBRL tags"""
    
    IX_NS = "{http://www.xbrl.org/2013/inlineXBRL}"
    
    if tag_type in ['nonFraction', 'numeric']:
        elem = ET.SubElement(parent, f'{IX_NS}nonFraction')
        elem.set('name', name)
        elem.set('contextRef', context_ref)
        if unit_ref:
            elem.set('unitRef', unit_ref)
        elem.set('decimals', str(decimals) if decimals is not None else '0')
        
        # Set the value
        try:
            num_val = float(value)
            elem.text = f"{num_val:,.0f}" if decimals == '0' else f"{num_val:,.2f}"
        except:
            elem.text = str(value)
    
    elif tag_type in ['nonNumeric', 'text']:
        elem = ET.SubElement(parent, f'{IX_NS}nonNumeric')
        elem.set('name', name)
        elem.set('contextRef', context_ref)
        elem.set('{http://www.w3.org/XML/1998/namespace}lang', xml_lang or 'en')
        
        # Set the value with escaping
        text = str(value) if value else ""
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        elem.text = text
    
    return elem

# Now test it
print("🧪 Testing minimal iXBRL generation...")

# Register namespaces
ET.register_namespace('', 'http://www.w3.org/1999/xhtml')
ET.register_namespace('ix', 'http://www.xbrl.org/2013/inlineXBRL')

# Create a simple structure
root = ET.Element('html', {
    'xmlns': 'http://www.w3.org/1999/xhtml',
    'xmlns:ix': 'http://www.xbrl.org/2013/inlineXBRL'
})

body = ET.SubElement(root, 'body')
div = ET.SubElement(body, 'div')

# Add a paragraph with iXBRL facts
p1 = ET.SubElement(div, 'p')
p1.text = 'Company name: '
create_enhanced_xbrl_tag(p1, 'nonNumeric', 'esrs:EntityName', 'c1', 'Test Corp')

p2 = ET.SubElement(div, 'p')
p2.text = 'Scope 1 emissions: '
create_enhanced_xbrl_tag(p2, 'nonFraction', 'esrs:Scope1', 'c1', 1500, unit_ref='tCO2e')
span = ET.SubElement(p2, 'span')
span.text = ' tonnes CO2e'

# Convert to string
xml_str = ET.tostring(root, encoding='unicode')

# Save
with open('minimal_test.xhtml', 'w') as f:
    f.write('<!DOCTYPE html>\n' + xml_str)

print("✅ Created minimal_test.xhtml")

# Verify
import re
fractions = len(re.findall(r'<ix:nonFraction', xml_str))
numerics = len(re.findall(r'<ix:nonNumeric', xml_str))

print(f"\n📊 Results:")
print(f"   Numeric facts: {fractions}")
print(f"   Text facts: {numerics}")
print(f"   Total: {fractions + numerics}")

if fractions > 0 and numerics > 0:
    print("\n✅ SUCCESS! iXBRL tags are working!")
    print("\nNow copy this create_enhanced_xbrl_tag function to your esrs_e1_full.py")
else:
    print("\n❌ Something went wrong")

# Show the content
print("\n📄 Generated content preview:")
print(xml_str[:500])