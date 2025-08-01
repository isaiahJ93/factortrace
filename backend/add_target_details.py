with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find E1-4 function and add target details
for i, line in enumerate(lines):
    if 'base_div.tail = " tCO₂e"' in line:
        print(f"Found base year info at line {i+1}, adding target details")
        
        indent = len(line) - len(line.lstrip())
        spaces = ' ' * indent
        
        target_details = f'''
{spaces}
{spaces}# Add target details
{spaces}target_details_div = ET.SubElement(section, 'div', attrib={{'class': 'target-details'}})
{spaces}
{spaces}# Target type
{spaces}p_type = ET.SubElement(target_details_div, 'p')
{spaces}p_type.text = "Target type: "
{spaces}type_elem = ET.SubElement(p_type, f'{{{{namespaces["ix"]}}}}}nonNumeric', attrib={{
{spaces}    'name': 'esrs-e1:TargetType',
{spaces}    'contextRef': 'current-period'
{spaces}}})
{spaces}type_elem.text = 'Absolute reduction'
{spaces}
{spaces}# Target year
{spaces}p_year = ET.SubElement(target_details_div, 'p')
{spaces}p_year.text = "Target year: "
{spaces}year_elem = ET.SubElement(p_year, f'{{{{namespaces["ix"]}}}}}nonFraction', attrib={{
{spaces}    'name': 'esrs-e1:TargetYear',
{spaces}    'contextRef': 'current-period',
{spaces}    'decimals': '0'
{spaces}}})
{spaces}year_elem.text = '2030'
{spaces}
{spaces}# Target reduction percentage
{spaces}p_reduction = ET.SubElement(target_details_div, 'p')
{spaces}p_reduction.text = "Target reduction: "
{spaces}reduction_elem = ET.SubElement(p_reduction, f'{{{{namespaces["ix"]}}}}}nonFraction', attrib={{
{spaces}    'name': 'esrs-e1:TargetReductionPercentage',
{spaces}    'contextRef': 'current-period',
{spaces}    'unitRef': 'percentage',
{spaces}    'decimals': '1'
{spaces}}})
{spaces}reduction_elem.text = '42.0'
{spaces}
{spaces}# Net-zero target
{spaces}p_netzero = ET.SubElement(target_details_div, 'p')
{spaces}p_netzero.text = "Net-zero target year: "
{spaces}netzero_elem = ET.SubElement(p_netzero, f'{{{{namespaces["ix"]}}}}}nonFraction', attrib={{
{spaces}    'name': 'esrs-e1:NetZeroTargetYear',
{spaces}    'contextRef': 'current-period',
{spaces}    'decimals': '0'
{spaces}}})
{spaces}netzero_elem.text = '2050'
'''
        lines.insert(i + 1, target_details)
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added enhanced target details to E1-4!")
