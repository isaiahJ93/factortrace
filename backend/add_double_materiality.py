with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find where we call create_e1_1
for i, line in enumerate(lines):
    if 'create_e1_1_transition_plan(body, data)' in line:
        print(f"Found E1-1 at line {i+1}")
        # Add double materiality after it
        indent = len(line) - len(line.lstrip())
        new_line = ' ' * indent + 'create_double_materiality_section(body, data)\n'
        lines.insert(i + 1, new_line)
        break

# Now add the function itself - find a good place
for i, line in enumerate(lines):
    if 'def create_e1_2_policies(body: ET.Element' in line:
        print(f"Found E1-2 function at line {i+1}, adding double materiality before it")
        
        func_code = '''def create_double_materiality_section(body: ET.Element, data: Dict[str, Any]) -> None:
    """Create double materiality assessment section"""
    section = ET.SubElement(body, 'section', attrib={
        'id': 'double-materiality',
        'class': 'disclosure-section'
    })
    
    h2 = ET.SubElement(section, 'h2')
    h2.text = "Double Materiality Assessment"
    
    # Environmental impact
    p1 = ET.SubElement(section, 'p')
    p1.text = "Environmental impact materiality: "
    impact_elem = ET.SubElement(p1, f'{{{namespaces["ix"]}}}nonNumeric', attrib={
        'name': 'esrs:EnvironmentalImpactMaterial',
        'contextRef': 'current-period'
    })
    impact_elem.text = 'true'
    
    # Financial impact
    p2 = ET.SubElement(section, 'p')
    p2.text = "Financial impact materiality: "
    financial_elem = ET.SubElement(p2, f'{{{namespaces["ix"]}}}nonNumeric', attrib={
        'name': 'esrs:FinancialImpactMaterial',
        'contextRef': 'current-period'
    })
    financial_elem.text = 'true'
    
    # Narrative
    p3 = ET.SubElement(section, 'p')
    narrative_elem = ET.SubElement(p3, f'{{{namespaces["ix"]}}}nonNumeric', attrib={
        'name': 'esrs:DoubleMaterialityAssessmentNarrative',
        'contextRef': 'current-period'
    })
    narrative_elem.text = 'Climate change identified as material through stakeholder engagement and impact assessment.'

'''
        lines.insert(i, func_code + '\n')
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added double materiality section!")
