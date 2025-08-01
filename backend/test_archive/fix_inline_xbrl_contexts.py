import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find and replace the contexts section we just added
old_context_pattern = r'# Add XBRL contexts and units in body before closing[\s\S]*?tree = ET\.ElementTree\(html\)'

new_contexts = '''# Add XBRL contexts and units in body before closing
    contexts_div = ET.SubElement(body, 'div', attrib={'style': 'display:none'})
    
    # Add ix:header with references
    ix_header = ET.SubElement(contexts_div, f'{{{namespaces["ix"]}}}header')
    ix_hidden = ET.SubElement(ix_header, f'{{{namespaces["ix"]}}}hidden')
    
    # Current instant context
    ctx1 = ET.SubElement(ix_hidden, f'{{{namespaces["ix"]}}}context', attrib={'id': 'current-instant'})
    entity1 = ET.SubElement(ctx1, f'{{{namespaces["xbrli"]}}}entity')
    id1 = ET.SubElement(entity1, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://standards.iso.org/iso/17442'})
    id1.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period1 = ET.SubElement(ctx1, f'{{{namespaces["xbrli"]}}}period')
    instant1 = ET.SubElement(period1, f'{{{namespaces["xbrli"]}}}instant')
    instant1.text = f"{data.get('reporting_period', 2025)}-12-31"
    
    # Current period context
    ctx2 = ET.SubElement(ix_hidden, f'{{{namespaces["ix"]}}}context', attrib={'id': 'current-period'})
    entity2 = ET.SubElement(ctx2, f'{{{namespaces["xbrli"]}}}entity')
    id2 = ET.SubElement(entity2, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://standards.iso.org/iso/17442'})
    id2.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period2 = ET.SubElement(ctx2, f'{{{namespaces["xbrli"]}}}period')
    start2 = ET.SubElement(period2, f'{{{namespaces["xbrli"]}}}startDate')
    start2.text = f"{data.get('reporting_period', 2025)}-01-01"
    end2 = ET.SubElement(period2, f'{{{namespaces["xbrli"]}}}endDate')
    end2.text = f"{data.get('reporting_period', 2025)}-12-31"
    
    # c-current context (for enhanced sections)
    ctx3 = ET.SubElement(ix_hidden, f'{{{namespaces["ix"]}}}context', attrib={'id': 'c-current'})
    entity3 = ET.SubElement(ctx3, f'{{{namespaces["xbrli"]}}}entity')
    id3 = ET.SubElement(entity3, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://standards.iso.org/iso/17442'})
    id3.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period3 = ET.SubElement(ctx3, f'{{{namespaces["xbrli"]}}}period')
    instant3 = ET.SubElement(period3, f'{{{namespaces["xbrli"]}}}instant')
    instant3.text = f"{data.get('reporting_period', 2025)}-12-31"
    
    # c-base context (base year)
    ctx4 = ET.SubElement(ix_hidden, f'{{{namespaces["ix"]}}}context', attrib={'id': 'c-base'})
    entity4 = ET.SubElement(ctx4, f'{{{namespaces["xbrli"]}}}entity')
    id4 = ET.SubElement(entity4, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://standards.iso.org/iso/17442'})
    id4.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period4 = ET.SubElement(ctx4, f'{{{namespaces["xbrli"]}}}period')
    instant4 = ET.SubElement(period4, f'{{{namespaces["xbrli"]}}}instant')
    base_year = data.get('targets', {}).get('base_year', data.get('reporting_period', 2025))
    instant4.text = f"{base_year}-12-31"
    
    # Units
    unit1 = ET.SubElement(ix_hidden, f'{{{namespaces["ix"]}}}unit', attrib={'id': 'tCO2e'})
    measure1 = ET.SubElement(unit1, f'{{{namespaces["xbrli"]}}}measure')
    measure1.text = 'esrs-e1:tCO2e'
    
    unit2 = ET.SubElement(ix_hidden, f'{{{namespaces["ix"]}}}unit', attrib={'id': 'u-tCO2e'})
    measure2 = ET.SubElement(unit2, f'{{{namespaces["xbrli"]}}}measure')
    measure2.text = 'esrs-e1:tCO2e'
    
    unit3 = ET.SubElement(ix_hidden, f'{{{namespaces["ix"]}}}unit', attrib={'id': 'tonnes'})
    measure3 = ET.SubElement(unit3, f'{{{namespaces["xbrli"]}}}measure')
    measure3.text = 'xbrli:tonnes'
    
    unit4 = ET.SubElement(ix_hidden, f'{{{namespaces["ix"]}}}unit', attrib={'id': 'mwh'})
    measure4 = ET.SubElement(unit4, f'{{{namespaces["xbrli"]}}}measure')
    measure4.text = 'esrs-e1:MWh'
    
    unit5 = ET.SubElement(ix_hidden, f'{{{namespaces["ix"]}}}unit', attrib={'id': 'EUR'})
    measure5 = ET.SubElement(unit5, f'{{{namespaces["xbrli"]}}}measure')
    measure5.text = 'iso4217:EUR'
    
    unit6 = ET.SubElement(ix_hidden, f'{{{namespaces["ix"]}}}unit', attrib={'id': 'percentage'})
    measure6 = ET.SubElement(unit6, f'{{{namespaces["xbrli"]}}}measure')
    measure6.text = 'xbrli:pure'
    
    tree = ET.ElementTree(html)'''

content = re.sub(old_context_pattern, new_contexts, content, flags=re.DOTALL)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed to use proper inline XBRL format with ix:context and ix:unit")
print("✅ Changed LEI scheme to ISO 17442 standard")
print("✅ Wrapped in ix:header/ix:hidden as required")
