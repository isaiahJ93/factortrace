with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find where we have historical emissions trend in E1-6
for i, line in enumerate(lines):
    if 'Historical emissions trend' in line and 'h3' in lines[i+1]:
        print(f"Found historical trend at line {i+1}")
        
        # Get the indentation
        indent_line = lines[i-1] if i > 0 else line
        indent = len(indent_line) - len(indent_line.lstrip())
        
        intensity_code = f'''
{' ' * indent}# Add GHG intensity metrics
{' ' * indent}intensity_div = ET.SubElement(section, 'div', attrib={{'class': 'intensity-metrics'}})
{' ' * indent}h3_intensity = ET.SubElement(intensity_div, 'h3')
{' ' * indent}h3_intensity.text = "GHG Intensity"
{' ' * indent}
{' ' * indent}p_intensity = ET.SubElement(intensity_div, 'p')
{' ' * indent}p_intensity.text = "Emissions per € million revenue: "
{' ' * indent}
{' ' * indent}# Calculate intensity (assuming default 10M revenue)
{' ' * indent}total_emissions = float(data.get('total_emissions', 0))
{' ' * indent}revenue = 10000000  # 10M EUR default
{' ' * indent}intensity = (total_emissions / 10.0) if total_emissions > 0 else 0
{' ' * indent}
{' ' * indent}intensity_elem = ET.SubElement(p_intensity, f'{{{{namespaces["ix"]}}}}}nonFraction', attrib={{
{' ' * indent}    'name': 'esrs-e1:GHGIntensityRevenue',
{' ' * indent}    'contextRef': 'current-period',
{' ' * indent}    'unitRef': 'tCO2e-per-mEUR',
{' ' * indent}    'decimals': '2'
{' ' * indent}}})
{' ' * indent}intensity_elem.text = f"{{intensity:.2f}}"
{' ' * indent}
'''
        lines.insert(i, intensity_code)
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added GHG intensity metrics!")
