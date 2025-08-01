with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find create_e1_5_energy_consumption
for i, line in enumerate(lines):
    if 'def create_e1_5_energy_consumption' in line:
        # Look for the first line after docstring
        j = i + 1
        # Skip docstring if exists
        if j < len(lines) and '"""' in lines[j]:
            while j < len(lines) and not lines[j].strip().endswith('"""'):
                j += 1
            j += 1
        
        # Check if namespaces already exists
        already_has = False
        for k in range(j, min(j+5, len(lines))):
            if 'namespaces = get_namespace_map()' in lines[k]:
                already_has = True
                break
        
        if not already_has:
            # Add namespaces
            lines.insert(j, '    namespaces = get_namespace_map()\n')
            print(f"✅ Added namespaces to create_e1_5_energy_consumption at line {j+1}")
        else:
            print("❌ Function already has namespaces")
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)
