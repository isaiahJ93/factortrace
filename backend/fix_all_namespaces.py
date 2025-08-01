# fix_all_namespaces.py
import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find all functions that use namespaces but don't define it
functions_to_fix = []

# Pattern to find functions using namespaces
pattern = r'def (\w+)\([^)]*\):[^}]*?namespaces\['

for match in re.finditer(pattern, content, re.DOTALL):
    func_name = match.group(1)
    # Check if this function already has namespaces = get_namespace_map()
    func_start = match.start()
    func_content = content[func_start:func_start+1000]
    if 'namespaces = get_namespace_map()' not in func_content and 'namespaces =' not in func_content[:200]:
        functions_to_fix.append(func_name)

print(f"Functions that need namespace fix: {functions_to_fix}")

# Add namespaces = get_namespace_map() to each function
for func_name in functions_to_fix:
    # Find the function definition
    pattern = rf'(def {func_name}\([^)]*\):[^{{]*?)([\n\s]+)(["\'].*?["\'][\n\s]+)?(.*?)(\n\s+\w)'
    
    def replacer(match):
        return match.group(1) + match.group(2) + (match.group(3) or '') + '    namespaces = get_namespace_map()\n' + match.group(4) + match.group(5)
    
    content = re.sub(pattern, replacer, content, flags=re.DOTALL)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed namespaces in all functions")