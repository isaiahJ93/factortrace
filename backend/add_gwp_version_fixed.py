with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find methodology section
for i, line in enumerate(lines):
    if 'p_ghg.text = "GHG Protocol aligned: True"' in line:
        print(f"Found methodology at line {i+1}, adding GWP version")
        
        indent = len(line) - len(line.lstrip())
        spaces = ' ' * indent
        
        gwp_code = f'''
{spaces}
{spaces}# GWP version
{spaces}namespaces = get_namespace_map()
{spaces}p_gwp = ET.SubElement(section, 'p')
{spaces}p_gwp.text = "GWP version used: "
{spaces}gwp_elem = ET.SubElement(p_gwp, namespaces["ix"] + 'nonNumeric', attrib={{
{spaces}    'name': 'esrs-e1:GWPVersionUsed',
{spaces}    'contextRef': 'current-period'
{spaces}}})
{spaces}gwp_elem.text = 'AR6'
'''
        lines.insert(i + 1, gwp_code)
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added GWP version to methodology!")
