with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Fix the duplicate namespaces line
content = content.replace(
    'namespaces = get_namespace_map()    namespaces = get_namespace_map()',
    'namespaces = get_namespace_map()'
)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed duplicate namespaces line")
