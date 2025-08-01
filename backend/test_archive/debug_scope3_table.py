import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Add logging after scope3_breakdown assignment
pattern = r'(scope3_breakdown = data\.get\(\'scope3_breakdown\', \{\}\))'
replacement = r'''\1
    print(f"DEBUG: scope3_breakdown = {scope3_breakdown}")
    print(f"DEBUG: bool(scope3_breakdown) = {bool(scope3_breakdown)}")
    print(f"DEBUG: type(scope3_breakdown) = {type(scope3_breakdown)}")'''

content = re.sub(pattern, replacement, content, count=1)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Added debug logging for scope3_breakdown")
