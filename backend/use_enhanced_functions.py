import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Update create_e1_2_policies to use add_climate_policy_section_enhanced
content = re.sub(
    r'def create_e1_2_policies\(body: ET\.Element, data: Dict\[str, Any\]\) -> None:[\s\S]*?p\.text = f"E1 2 Policies - To be implemented"',
    '''def create_e1_2_policies(body: ET.Element, data: Dict[str, Any]) -> None:
    """Create E1-2 Policies section using enhanced function"""
    add_climate_policy_section_enhanced(body, data)''',
    content
)

# Update create_e1_3_actions_resources to use add_climate_actions_section_enhanced
content = re.sub(
    r'def create_e1_3_actions_resources\(body: ET\.Element, data: Dict\[str, Any\]\) -> None:[\s\S]*?p\.text = f"E1 3 Actions Resources - To be implemented"',
    '''def create_e1_3_actions_resources(body: ET.Element, data: Dict[str, Any]) -> None:
    """Create E1-3 Actions section using enhanced function"""
    add_climate_actions_section_enhanced(body, data)''',
    content
)

# Update create_e1_4_targets - need to find the right function name first
print("Searching for E1-4 function...")
if 'add_climate_targets_section_enhanced' in content:
    content = re.sub(
        r'def create_e1_4_targets\(body: ET\.Element, data: Dict\[str, Any\]\) -> None:[\s\S]*?p\.text = f"E1 4 Targets - To be implemented"',
        '''def create_e1_4_targets(body: ET.Element, data: Dict[str, Any]) -> None:
    """Create E1-4 Targets section using enhanced function"""
    add_climate_targets_section_enhanced(body, data)''',
        content
    )
else:
    # Search for the actual targets function
    import re as re2
    matches = re2.findall(r'def (add_[^(]*targets[^(]*)\(', content)
    if matches:
        print(f"Found targets function: {matches[0]}")
        content = re.sub(
            r'def create_e1_4_targets\(body: ET\.Element, data: Dict\[str, Any\]\) -> None:[\s\S]*?p\.text = f"E1 4 Targets - To be implemented"',
            f'''def create_e1_4_targets(body: ET.Element, data: Dict[str, Any]) -> None:
    """Create E1-4 Targets section using enhanced function"""
    {matches[0]}(body, data)''',
            content
        )

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Connected stub functions to enhanced implementations")
