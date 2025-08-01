# fix_all_validations.py
import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Replace all direct dictionary access in validate_financial_effects with .get()
patterns = [
    (r"fe_data\['([^']+)'\]", r"fe_data.get('\1', {})"),
    (r"effects\['([^']+)'\]", r"effects.get('\1', 0)"),
    (r"if ([a-zA-Z_]+)\['([^']+)'\]:", r"if \1.get('\2'):"),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed all validation dictionary access issues")