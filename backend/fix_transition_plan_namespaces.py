with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find the function and add namespaces
for i, line in enumerate(lines):
    if 'def create_e1_1_transition_plan' in line:
        # Look for the first non-docstring, non-empty line
        j = i + 1
        # Skip docstring
        if j < len(lines) and '"""' in lines[j]:
            j += 1
            while j < len(lines) and '"""' not in lines[j]:
                j += 1
            j += 1
        
        # Add namespaces
        lines.insert(j, '    namespaces = get_namespace_map()\n')
        print(f"Added namespaces at line {j+1}")
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)
