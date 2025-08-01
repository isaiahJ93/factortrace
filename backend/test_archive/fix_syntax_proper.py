with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find the problematic line and fix it
for i, line in enumerate(lines):
    if "namespaces = get_namespace_map()        'id': 'e1-1'," in line:
        # Replace this line with the proper structure
        lines[i] = "        'id': 'e1-1',\n"
        # Insert namespaces in the right place (after the docstring)
        lines.insert(i-1, "    namespaces = get_namespace_map()\n")
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed syntax and moved namespaces to correct location")
