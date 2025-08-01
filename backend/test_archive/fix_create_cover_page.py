with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find create_cover_page function at line 282 (index 281)
if 'def create_cover_page' in lines[281]:
    # Find where to insert (after the function definition and any docstring)
    i = 282
    # Skip docstring if present
    if '"""' in lines[i]:
        while i < len(lines) and '"""' not in lines[i].strip():
            i += 1
        i += 1
    
    # Insert namespaces line
    lines.insert(i, '    namespaces = get_namespace_map()\n')
    print(f"✅ Added namespaces at line {i+1}")

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)
