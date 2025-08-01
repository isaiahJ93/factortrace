import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find all function definitions that contain 'namespaces[' in their body
pattern = r'(def\s+\w+\s*\([^)]*\)\s*:\s*\n(?:\s*""".*?"""\s*\n)?)((?:.*?\n)*?)(?=\ndef\s|\nclass\s|\Z)'

def process_function(match):
    header = match.group(1)
    body = match.group(2)
    
    # Check if this function uses namespaces
    if 'namespaces[' in body and 'namespaces = get_namespace_map()' not in body:
        # Add namespaces after header
        return header + '    namespaces = get_namespace_map()\n' + body
    return match.group(0)

content = re.sub(pattern, process_function, content, flags=re.MULTILINE | re.DOTALL)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Added namespaces to all functions that need it")
