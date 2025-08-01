with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find and replace the stub function bodies
in_e1_2 = False
in_e1_3 = False
in_e1_4 = False
new_lines = []

for i, line in enumerate(lines):
    # Detect which function we're in
    if 'def create_e1_2_policies' in line:
        in_e1_2 = True
        in_e1_3 = False
        in_e1_4 = False
    elif 'def create_e1_3_actions_resources' in line:
        in_e1_2 = False
        in_e1_3 = True
        in_e1_4 = False
    elif 'def create_e1_4_targets' in line:
        in_e1_2 = False
        in_e1_3 = False
        in_e1_4 = True
    elif line.strip().startswith('def '):
        in_e1_2 = False
        in_e1_3 = False
        in_e1_4 = False
    
    # Replace the stub implementations
    if in_e1_2 and 'add_climate_policy_section_enhanced(body, data)' in line:
        # Already fixed
        new_lines.append(line)
    elif in_e1_2 and ('E1 2 Policies - To be implemented' in line or 'namespaces = get_namespace_map()' in line):
        # Skip these lines, we'll add the function call
        if 'namespaces = get_namespace_map()' in line:
            new_lines.append('    add_climate_policy_section_enhanced(body, data)\n')
    elif in_e1_3 and 'add_climate_actions_section_enhanced(body, data)' in line:
        # Already fixed
        new_lines.append(line)
    elif in_e1_3 and ('E1 3 Actions Resources - To be implemented' in line or 'namespaces = get_namespace_map()' in line):
        # Skip these lines, we'll add the function call
        if 'namespaces = get_namespace_map()' in line:
            new_lines.append('    add_climate_actions_section_enhanced(body, data)\n')
    elif in_e1_4 and ('targets_section =' in line or 'h2.text = "E1-4:' in line or '42% by 2030' in line):
        # Skip the manual implementation
        if 'targets_section =' in line:
            new_lines.append('    add_targets_section(body, data)\n')
    else:
        new_lines.append(line)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Fixed all section stubs to use enhanced functions")
