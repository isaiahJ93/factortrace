import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find all functions that use namespaces[...] but don't have namespaces = get_namespace_map()
pattern = r'def\s+(\w+)\s*\([^)]*\)\s*:\s*\n(?:.*?\n)*?.*?namespaces\[.*?\]'

matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))

functions_to_fix = []
for match in matches:
    func_name = match.group(1)
    func_content = match.group(0)
    
    # Check if this function already has namespaces = get_namespace_map()
    if 'namespaces = get_namespace_map()' not in func_content:
        functions_to_fix.append(func_name)

print(f"Functions needing namespace fix: {functions_to_fix[:10]}...")  # Show first 10

# Fix each function by adding namespaces after the docstring
for func_name in functions_to_fix:
    # Pattern to match function definition and optional docstring
    pattern = rf'(def\s+{func_name}\s*\([^)]*\)\s*:\s*\n)(\s*""".*?"""\s*\n)?'
    
    def replacer(match):
        func_def = match.group(1)
        docstring = match.group(2) or ''
        return func_def + docstring + '    namespaces = get_namespace_map()\n'
    
    content = re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print(f"✅ Fixed namespaces in {len(functions_to_fix)} functions")
