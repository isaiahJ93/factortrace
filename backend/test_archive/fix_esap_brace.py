# fix_esap_brace.py
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Replace the pattern to add the missing closing brace
content = content.replace(
    '    }\nfrom enum import Enum',
    '    }\n}\n\nfrom enum import Enum'
)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed ESAP_CONFIG - added closing brace!")