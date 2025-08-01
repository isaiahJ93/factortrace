with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find where we add units (after percentage unit)
for i, line in enumerate(lines):
    if "measure6.text = 'xbrli:pure'" in line:
        print(f"Found last unit at line {i+1}")
        
        # Get indentation
        indent = len(line) - len(line.lstrip())
        
        unit_code = f'''
{' ' * indent}
{' ' * indent}# Additional unit for intensity metrics
{' ' * indent}unit7 = ET.SubElement(contexts_div, f'{{{{namespaces["xbrli"]}}}}}unit', attrib={{'id': 'tCO2e-per-mEUR'}})
{' ' * indent}divide = ET.SubElement(unit7, f'{{{{namespaces["xbrli"]}}}}}divide')
{' ' * indent}numerator = ET.SubElement(divide, f'{{{{namespaces["xbrli"]}}}}}unitNumerator')
{' ' * indent}measure7_num = ET.SubElement(numerator, f'{{{{namespaces["xbrli"]}}}}}measure')
{' ' * indent}measure7_num.text = 'esrs-e1:tCO2e'
{' ' * indent}denominator = ET.SubElement(divide, f'{{{{namespaces["xbrli"]}}}}}unitDenominator')
{' ' * indent}measure7_den = ET.SubElement(denominator, f'{{{{namespaces["xbrli"]}}}}}measure')
{' ' * indent}measure7_den.text = 'esrs:millionEUR'
'''
        lines.insert(i + 1, unit_code)
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added tCO2e-per-mEUR unit!")
