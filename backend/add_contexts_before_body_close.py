import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find where we build the tree (this is right before </body></html>)
pattern = r'(\s+)(tree = ET\.ElementTree\(html\)\s+return tree)'

# Insert the contexts right before building the tree
insertion = r'''\1# Add XBRL contexts and units before closing body
\1contexts_div = ET.SubElement(body, 'div', attrib={'style': 'display:none'})
\1
\1# Current instant context
\1ctx1 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'current-instant'})
\1entity1 = ET.SubElement(ctx1, f'{{{namespaces["xbrli"]}}}entity')
\1id1 = ET.SubElement(entity1, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
\1id1.text = '529900HNOAA1KXQJUQ27'
\1period1 = ET.SubElement(ctx1, f'{{{namespaces["xbrli"]}}}period')
\1instant1 = ET.SubElement(period1, f'{{{namespaces["xbrli"]}}}instant')
\1instant1.text = '2025-12-31'
\1
\1# Current period context
\1ctx2 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'current-period'})
\1entity2 = ET.SubElement(ctx2, f'{{{namespaces["xbrli"]}}}entity')
\1id2 = ET.SubElement(entity2, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
\1id2.text = '529900HNOAA1KXQJUQ27'
\1period2 = ET.SubElement(ctx2, f'{{{namespaces["xbrli"]}}}period')
\1start2 = ET.SubElement(period2, f'{{{namespaces["xbrli"]}}}startDate')
\1start2.text = '2025-01-01'
\1end2 = ET.SubElement(period2, f'{{{namespaces["xbrli"]}}}endDate')
\1end2.text = '2025-12-31'
\1
\1# c-current context
\1ctx3 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'c-current'})
\1entity3 = ET.SubElement(ctx3, f'{{{namespaces["xbrli"]}}}entity')
\1id3 = ET.SubElement(entity3, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
\1id3.text = '529900HNOAA1KXQJUQ27'
\1period3 = ET.SubElement(ctx3, f'{{{namespaces["xbrli"]}}}period')
\1instant3 = ET.SubElement(period3, f'{{{namespaces["xbrli"]}}}instant')
\1instant3.text = '2025-12-31'
\1
\1# c-base context
\1ctx4 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}context', attrib={'id': 'c-base'})
\1entity4 = ET.SubElement(ctx4, f'{{{namespaces["xbrli"]}}}entity')
\1id4 = ET.SubElement(entity4, f'{{{namespaces["xbrli"]}}}identifier', attrib={'scheme': 'http://www.lei-worldwide.com'})
\1id4.text = '529900HNOAA1KXQJUQ27'
\1period4 = ET.SubElement(ctx4, f'{{{namespaces["xbrli"]}}}period')
\1instant4 = ET.SubElement(period4, f'{{{namespaces["xbrli"]}}}instant')
\1instant4.text = '2025-12-31'
\1
\1# Units
\1unit1 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'tCO2e'})
\1measure1 = ET.SubElement(unit1, f'{{{namespaces["xbrli"]}}}measure')
\1measure1.text = 'esrs-e1:tCO2e'
\1
\1unit2 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'u-tCO2e'})
\1measure2 = ET.SubElement(unit2, f'{{{namespaces["xbrli"]}}}measure')
\1measure2.text = 'esrs-e1:tCO2e'
\1
\1unit3 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'tonnes'})
\1measure3 = ET.SubElement(unit3, f'{{{namespaces["xbrli"]}}}measure')
\1measure3.text = 'esrs-e1:tonnes'
\1
\1unit4 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'mwh'})
\1measure4 = ET.SubElement(unit4, f'{{{namespaces["xbrli"]}}}measure')
\1measure4.text = 'esrs-e1:MWh'
\1
\1unit5 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'EUR'})
\1measure5 = ET.SubElement(unit5, f'{{{namespaces["xbrli"]}}}measure')
\1measure5.text = 'iso4217:EUR'
\1
\1unit6 = ET.SubElement(contexts_div, f'{{{namespaces["xbrli"]}}}unit', attrib={'id': 'percentage'})
\1measure6 = ET.SubElement(unit6, f'{{{namespaces["xbrli"]}}}measure')
\1measure6.text = 'xbrli:pure'
\1
\1\2'''

# Replace ALL occurrences
content = re.sub(pattern, insertion, content)

# Count how many replacements
import re as re2
matches = len(re2.findall(pattern, content))
print(f"Found {matches} places to add contexts")

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Added XBRL contexts and units RIGHT BEFORE closing body!")
