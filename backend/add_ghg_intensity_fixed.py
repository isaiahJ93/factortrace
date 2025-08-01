with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find where we have historical emissions trend in E1-6
for i, line in enumerate(lines):
    if 'Historical emissions trend' in line and i+1 < len(lines) and 'h3' in lines[i+1]:
        print(f"Found historical trend at line {i+1}")
        
        # Get the indentation
        indent_line = lines[i-1] if i > 0 else line
        indent = len(indent_line) - len(indent_line.lstrip())
        spaces = ' ' * indent
        
        intensity_code = f'''
{spaces}# Add GHG intensity metrics
{spaces}intensity_div = ET.SubElement(section, 'div', attrib={{'class': 'intensity-metrics'}})
{spaces}h3_intensity = ET.SubElement(intensity_div, 'h3')
{spaces}h3_intensity.text = "GHG Intensity"
{spaces}
{spaces}p_intensity = ET.SubElement(intensity_div, 'p')
{spaces}p_intensity.text = "Emissions per € million revenue: "
{spaces}
{spaces}# Calculate intensity (assuming default 10M revenue)
{spaces}total_emissions = float(data.get('total_emissions', 0))
{spaces}revenue = 10000000  # 10M EUR default
{spaces}intensity = (total_emissions / 10.0) if total_emissions > 0 else 0
{spaces}
{spaces}intensity_elem = ET.SubElement(p_intensity, 'ix:nonFraction', attrib={{
{spaces}    'name': 'esrs-e1:GHGIntensityRevenue',
{spaces}    'contextRef': 'current-period',
{spaces}    'unitRef': 'tCO2e-per-mEUR',
{spaces}    'decimals': '2'
{spaces}}})
{spaces}intensity_elem.text = str(round(intensity, 2))
{spaces}
'''
        lines.insert(i, intensity_code)
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added GHG intensity metrics!")
