import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find where we have the appendices section and add contexts after it
pattern = r'(</div>\s*</section>)(\s*tree = ET\.ElementTree\(html\))'

replacement = r'''\1
    
    # Add XBRL contexts and units before closing body
    contexts_div = ET.SubElement(body, 'div', attrib={'style': 'display:none'})
    
    # Current instant context
    ctx1 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'current-instant'})
    entity1 = ET.SubElement(ctx1, f'{{{namespaces["xbrli"]}}}entity')
    id1 = ET.SubElement(entity1, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
    id1.text = '529900HNOAA1KXQJUQ27'
    period1 = ET.SubElement(ctx1, f'{{{namespaces["xbrli"]}}}period')
    instant1 = ET.SubElement(period1, f'{{{namespaces["xbrli"]}}}instant')
    instant1.text = '2025-12-31'
    
    # Current period context
    ctx2 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'current-period'})
    entity2 = ET.SubElement(ctx2, f'{{{namespaces["xbrli"]}}}entity')
    id2 = ET.SubElement(entity2, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
    id2.text = '529900HNOAA1KXQJUQ27'
    period2 = ET.SubElement(ctx2, f'{{{namespaces["xbrli"]}}}period')
    start2 = ET.SubElement(period2, f'{{{namespaces["xbrli"]}}}startDate')
    start2.text = '2025-01-01'
    end2 = ET.SubElement(period2, f'{{{namespaces["xbrli"]}}}endDate')
    end2.text = '2025-12-31'
    
    # c-current context
    ctx3 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'c-current'})
    entity3 = ET.SubElement(ctx3, f'{{{namespaces["xbrli"]}}}entity')
    id3 = ET.SubElement(entity3, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
    id3.text = '529900HNOAA1KXQJUQ27'
    period3 = ET.SubElement(ctx3, f'{{{namespaces["xbrli"]}}}period')
    instant3 = ET.SubElement(period3, f'{{{namespaces["xbrli"]}}}instant')
    instant3.text = '2025-12-31'
    
    # c-base context
    ctx4 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'c-base'})
    entity4 = ET.SubElement(ctx4, f'{{{namespaces["xbrli"]}}}entity')
    id4 = ET.SubElement(entity4, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
    id4.text = '529900HNOAA1KXQJUQ27'
    period4 = ET.SubElement(ctx4, f'{{{namespaces["xbrli"]}}}period')
    instant4 = ET.SubElement(period4, f'{{{namespaces["xbrli"]}}}instant')
    instant4.text = '2025-12-31'
    
    # Units
    unit1 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'tCO2e'})
    measure1 = ET.SubElement(unit1, f'{{{namespaces["xbrli"]}}}measure')
    measure1.text = 'esrs-e1:tCO2e'
    
    unit2 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'u-tCO2e'})
    measure2 = ET.SubElement(unit2, f'{{{namespaces["xbrli"]}}}measure')
    measure2.text = 'esrs-e1:tCO2e'
    
    unit3 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'tonnes'})
    measure3 = ET.SubElement(unit3, f'{{{namespaces["xbrli"]}}}measure')
    measure3.text = 'esrs-e1:tonnes'
    
    unit4 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'mwh'})
    measure4 = ET.SubElement(unit4, f'{{{namespaces["xbrli"]}}}measure')
    measure4.text = 'esrs-e1:MWh'
    
    unit5 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'EUR'})
    measure5 = ET.SubElement(unit5, f'{{{namespaces["xbrli"]}}}measure')
    measure5.text = 'iso4217:EUR'
    
    unit6 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'percentage'})
    measure6 = ET.SubElement(unit6, f'{{{namespaces["xbrli"]}}}measure')
    measure6.text = 'xbrli:pure'
    
\2'''

# Try to find and replace
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    print("✅ Found and replaced the pattern!")
else:
    print("❌ Pattern not found. Let me try a different approach...")
    # Alternative: find where appendices end
    alt_pattern = r'(</div>\s*</section>\s*)(tree = ET\.ElementTree)'
    if re.search(alt_pattern, content, re.DOTALL):
        content = re.sub(alt_pattern, replacement, content, flags=re.DOTALL)
        print("✅ Used alternative pattern!")

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)
