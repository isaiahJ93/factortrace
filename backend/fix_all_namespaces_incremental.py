import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Keep track of functions we've fixed
fixed_count = 0

# Process line by line
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this is a function definition
    if line.strip().startswith('def '):
        func_start = i
        func_name = line.split('(')[0].replace('def ', '').strip()
        
        # Look ahead to see if this function uses namespaces
        uses_namespaces = False
        has_namespace_def = False
        
        j = i + 1
        # Skip docstring if present
        if j < len(lines) and '"""' in lines[j]:
            while j < len(lines) and not lines[j].strip().endswith('"""'):
                j += 1
            j += 1
        
        # Check next 50 lines for namespace usage
        for k in range(j, min(j + 50, len(lines))):
            if 'namespaces[' in lines[k]:
                uses_namespaces = True
            if 'namespaces = get_namespace_map()' in lines[k]:
                has_namespace_def = True
                break
            if k < len(lines) and lines[k].strip() and not lines[k].startswith(' '):
                break  # Hit next function/class
        
        # If uses namespaces but doesn't define it, add it
        if uses_namespaces and not has_namespace_def:
            lines.insert(j, '    namespaces = get_namespace_map()\n')
            fixed_count += 1
            print(f"Fixed: {func_name}")
            i = j  # Skip ahead
    
    i += 1

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print(f"\n✅ Fixed {fixed_count} functions")
