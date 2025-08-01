import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find all functions that use namespaces[...] but don't define it
pattern = r'def ([^(]+)\([^)]*\):[^}]*?namespaces\[["\']'
matches = list(re.finditer(pattern, content, re.DOTALL))

functions_to_fix = []
for match in matches:
    func_name = match.group(1)
    func_start = match.start()
    # Check if this function already has namespaces = get_namespace_map()
    func_end = content.find('\ndef ', func_start + 1)
    if func_end == -1:
        func_end = len(content)
    func_content = content[func_start:func_end]
    
    if 'namespaces = get_namespace_map()' not in func_content:
        functions_to_fix.append(func_name)

print(f"Functions needing namespace fix: {functions_to_fix}")

# Fix each function
for func_name in functions_to_fix:
    # Find function and add namespaces after docstring
    pattern = rf'(def {func_name}\([^)]*\):[^\n]*\n)((?:\s*"""[^"]*"""\n)?)'
    replacement = r'\1\2    namespaces = get_namespace_map()\n'
    content = re.sub(pattern, replacement, content)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print(f"✅ Fixed {len(functions_to_fix)} functions")
