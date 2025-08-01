#!/usr/bin/env python3
"""
Fix the minimal test to avoid duplicate xmlns:ix
"""

import xml.etree.ElementTree as ET
from typing import Any, Optional

# Working create_enhanced_xbrl_tag function
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

print("🧪 Creating fixed minimal iXBRL test...")

# Register namespaces BEFORE creating elements
ET.register_namespace('', 'http://www.w3.org/1999/xhtml')
ET.register_namespace('ix', 'http://www.xbrl.org/2013/inlineXBRL')
ET.register_namespace('xbrli', 'http://www.xbrl.org/2003/instance')

# Create root with namespaces
root = ET.Element('{http://www.w3.org/1999/xhtml}html')
root.set('{http://www.w3.org/2000/xmlns/}ix', 'http://www.xbrl.org/2013/inlineXBRL')
root.set('{http://www.w3.org/2000/xmlns/}xbrli', 'http://www.xbrl.org/2003/instance')

# Create head
head = ET.SubElement(root, '{http://www.w3.org/1999/xhtml}head')
title = ET.SubElement(head, '{http://www.w3.org/1999/xhtml}title')
title.text = 'Fixed Minimal iXBRL Test'

# Create body
body = ET.SubElement(root, '{http://www.w3.org/1999/xhtml}body')

# Add hidden section for context and unit
hidden = ET.SubElement(body, '{http://www.xbrl.org/2013/inlineXBRL}hidden')
resources = ET.SubElement(hidden, '{http://www.xbrl.org/2013/inlineXBRL}resources')

# Add context
context = ET.SubElement(resources, '{http://www.xbrl.org/2003/instance}context', {'id': 'c1'})
entity = ET.SubElement(context, '{http://www.xbrl.org/2003/instance}entity')
identifier = ET.SubElement(entity, '{http://www.xbrl.org/2003/instance}identifier', {
    'scheme': 'http://standards.iso.org/iso/17442'
})
identifier.text = 'ABCDEFGHIJ1234567890'
period = ET.SubElement(context, '{http://www.xbrl.org/2003/instance}period')
instant = ET.SubElement(period, '{http://www.xbrl.org/2003/instance}instant')
instant.text = '2024-12-31'

# Add unit
unit = ET.SubElement(resources, '{http://www.xbrl.org/2003/instance}unit', {'id': 'tCO2e'})
measure = ET.SubElement(unit, '{http://www.xbrl.org/2003/instance}measure')
measure.text = 'esrs:tCO2e'

# Add visible content
div = ET.SubElement(body, '{http://www.w3.org/1999/xhtml}div')

# Add facts using the function
p1 = ET.SubElement(div, '{http://www.w3.org/1999/xhtml}p')
p1.text = 'Company name: '
create_enhanced_xbrl_tag(p1, 'nonNumeric', 'esrs:EntityName', 'c1', 'Test Corp')

p2 = ET.SubElement(div, '{http://www.w3.org/1999/xhtml}p')
p2.text = 'Scope 1 emissions: '
create_enhanced_xbrl_tag(p2, 'nonFraction', 'esrs:Scope1', 'c1', 1500, unit_ref='tCO2e')
span = ET.SubElement(p2, '{http://www.w3.org/1999/xhtml}span')
span.text = ' tonnes CO2e'

# Convert to string
xml_str = ET.tostring(root, encoding='unicode', method='xml')

# Clean up and add DOCTYPE
output = '<!DOCTYPE html>\n' + xml_str

# Save
with open('minimal_fixed.xhtml', 'w') as f:
    f.write(output)

print("✅ Created minimal_fixed.xhtml")

# Verify
import re
fractions = len(re.findall(r'<ix:nonFraction', output))
numerics = len(re.findall(r'<ix:nonNumeric', output))
contexts = len(re.findall(r'<xbrli:context', output))
units = len(re.findall(r'<xbrli:unit', output))

print(f"\n📊 Results:")
print(f"   Numeric facts: {fractions}")
print(f"   Text facts: {numerics}")
print(f"   Contexts: {contexts}")
print(f"   Units: {units}")
print(f"   Total facts: {fractions + numerics}")

if fractions > 0 and numerics > 0 and contexts > 0 and units > 0:
    print("\n✅ SUCCESS! Complete iXBRL structure created!")
else:
    print("\n❌ Something is missing")

print("\nNow verify with: python3 verify_ixbrl.py minimal_fixed.xhtml")