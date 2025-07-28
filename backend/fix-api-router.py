import re

# Read the API file
with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Replace voucher_simple with voucher
content = re.sub(r'module_path="voucher_simple"', 'module_path="voucher"', content)
content = re.sub(r'from \.endpoints import voucher_simple', 'from .endpoints import voucher', content)

# Write back
with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("Updated API to use full voucher module")
