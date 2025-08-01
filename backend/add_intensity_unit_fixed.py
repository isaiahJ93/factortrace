with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find where we add units (after percentage unit)
for i, line in enumerate(lines):
    if "measure6.text = 'xbrli:pure'" in line:
        print(f"Found last unit at line {i+1}")
        
        # Get indentation
        indent = len(line) - len(line.lstrip())
        spaces = ' ' * indent
        
        unit_code = f'''
{spaces}
{spaces}# Additional unit for intensity metrics
{spaces}unit7 = ET.SubElement(contexts_div, 'xbrli:unit', attrib={{'id': 'tCO2e-per-mEUR'}})
{spaces}divide = ET.SubElement(unit7, 'xbrli:divide')
{spaces}numerator = ET.SubElement(divide, 'xbrli:unitNumerator')
{spaces}measure7_num = ET.SubElement(numerator, 'xbrli:measure')
{spaces}measure7_num.text = 'esrs-e1:tCO2e'
{spaces}denominator = ET.SubElement(divide, 'xbrli:unitDenominator')
{spaces}measure7_den = ET.SubElement(denominator, 'xbrli:measure')
{spaces}measure7_den.text = 'esrs:millionEUR'
'''
        lines.insert(i + 1, unit_code)
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added tCO2e-per-mEUR unit!")
