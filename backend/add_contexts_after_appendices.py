with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find the line with create_appendices
appendices_line = None
for i, line in enumerate(lines):
    if 'create_appendices(body, data)' in line:
        appendices_line = i
        print(f"Found create_appendices at line {i+1}")
        break

if appendices_line is None:
    print("❌ Could not find create_appendices")
    exit(1)

# Insert the contexts after create_appendices
contexts_code = '''    
    # Add XBRL contexts and units before closing body
    contexts_div = ET.SubElement(body, 'div', attrib={'style': 'display:none'})
    
    # Current instant context
    ctx1 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'current-instant'})
    entity1 = ET.SubElement(ctx1, f'{{{namespaces["xbrli"]}}}entity')
    id1 = ET.SubElement(entity1, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
    id1.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period1 = ET.SubElement(ctx1, f'{{{namespaces["xbrli"]}}}period')
    instant1 = ET.SubElement(period1, f'{{{namespaces["xbrli"]}}}instant')
    instant1.text = f"{data.get('reporting_period', 2025)}-12-31"
    
    # Current period context
    ctx2 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'current-period'})
    entity2 = ET.SubElement(ctx2, f'{{{namespaces["xbrli"]}}}entity')
    id2 = ET.SubElement(entity2, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
    id2.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period2 = ET.SubElement(ctx2, f'{{{namespaces["xbrli"]}}}period')
    start2 = ET.SubElement(period2, f'{{{namespaces["xbrli"]}}}startDate')
    start2.text = f"{data.get('reporting_period', 2025)}-01-01"
    end2 = ET.SubElement(period2, f'{{{namespaces["xbrli"]}}}endDate')
    end2.text = f"{data.get('reporting_period', 2025)}-12-31"
    
    # c-current context
    ctx3 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'c-current'})
    entity3 = ET.SubElement(ctx3, f'{{{namespaces["xbrli"]}}}entity')
    id3 = ET.SubElement(entity3, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
    id3.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period3 = ET.SubElement(ctx3, f'{{{namespaces["xbrli"]}}}period')
    instant3 = ET.SubElement(period3, f'{{{namespaces["xbrli"]}}}instant')
    instant3.text = f"{data.get('reporting_period', 2025)}-12-31"
    
    # c-base context
    ctx4 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'c-base'})
    entity4 = ET.SubElement(ctx4, f'{{{namespaces["xbrli"]}}}entity')
    id4 = ET.SubElement(entity4, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
    id4.text = data.get('lei', '529900HNOAA1KXQJUQ27')
    period4 = ET.SubElement(ctx4, f'{{{namespaces["xbrli"]}}}period')
    instant4 = ET.SubElement(period4, f'{{{namespaces["xbrli"]}}}instant')
    base_year = data.get('targets', {}).get('base_year', data.get('reporting_period', 2025))
    instant4.text = f"{base_year}-12-31"
    
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
'''

# Insert after appendices line
lines.insert(appendices_line + 1, contexts_code + '\n')

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Successfully added XBRL contexts and units after appendices!")
