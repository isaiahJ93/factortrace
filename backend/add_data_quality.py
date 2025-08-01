with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Add to Scope 1 section
for i, line in enumerate(lines):
    if 'p_scope1.text = "Total Scope 1 emissions: "' in line:
        # Find where this paragraph ends
        j = i
        while j < len(lines) and 'h4' not in lines[j]:
            j += 1
        
        indent = len(lines[i]) - len(lines[i].lstrip())
        spaces = ' ' * indent
        
        quality_code = f'''
{spaces}
{spaces}# Data quality score
{spaces}p_quality1 = ET.SubElement(scope1_div, 'p')
{spaces}p_quality1.text = "Data quality score: "
{spaces}quality1_elem = ET.SubElement(p_quality1, f'{{{{namespaces["ix"]}}}}}nonFraction', attrib={{
{spaces}    'name': 'esrs-e1:Scope1DataQuality',
{spaces}    'contextRef': 'current-period',
{spaces}    'unitRef': 'pure',
{spaces}    'decimals': '1'
{spaces}}})
{spaces}quality1_elem.text = '4.0'  # High quality (1-5 scale, 5 = best)
'''
        lines.insert(j, quality_code)
        print(f"Added Scope 1 data quality at line {j}")
        break

# Add to Scope 2 section
for i, line in enumerate(lines):
    if 'p_market.text = "Market-based: "' in line:
        j = i + 5  # After market-based paragraph
        
        indent = len(lines[i]) - len(lines[i].lstrip())
        spaces = ' ' * indent
        
        quality_code = f'''
{spaces}
{spaces}# Data quality score
{spaces}p_quality2 = ET.SubElement(scope2_div, 'p')
{spaces}p_quality2.text = "Data quality score: "
{spaces}quality2_elem = ET.SubElement(p_quality2, f'{{{{namespaces["ix"]}}}}}nonFraction', attrib={{
{spaces}    'name': 'esrs-e1:Scope2DataQuality',
{spaces}    'contextRef': 'current-period',
{spaces}    'unitRef': 'pure',
{spaces}    'decimals': '1'
{spaces}}})
{spaces}quality2_elem.text = '3.5'
'''
        lines.insert(j, quality_code)
        print(f"Added Scope 2 data quality at line {j}")
        break

# Add to Scope 3 section  
for i, line in enumerate(lines):
    if 'p_scope3.text = "Total Scope 3 emissions: "' in line:
        j = i + 5
        
        indent = len(lines[i]) - len(lines[i].lstrip())
        spaces = ' ' * indent
        
        quality_code = f'''
{spaces}
{spaces}# Data quality score
{spaces}p_quality3 = ET.SubElement(scope3_div, 'p')
{spaces}p_quality3.text = "Data quality score: "
{spaces}quality3_elem = ET.SubElement(p_quality3, f'{{{{namespaces["ix"]}}}}}nonFraction', attrib={{
{spaces}    'name': 'esrs-e1:Scope3DataQuality',
{spaces}    'contextRef': 'current-period',
{spaces}    'unitRef': 'pure',
{spaces}    'decimals': '1'
{spaces}}})
{spaces}quality3_elem.text = '3.0'  # Lower quality due to estimates
'''
        lines.insert(j, quality_code)
        print(f"Added Scope 3 data quality at line {j}")
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added data quality scores to all scopes!")
