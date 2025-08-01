with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Fix 1: Close the dictionary before NACE_CODE_REGISTRY (line 58-59)
for i, line in enumerate(lines):
    if line.strip() == "NACE_CODE_REGISTRY = {" and i > 0:
        # Check if previous non-empty line has a closing brace
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        if j >= 0 and not lines[j].strip().endswith('}'):
            lines.insert(i, '}')
            print(f"Added closing brace before NACE_CODE_REGISTRY at line {i}")
            break

# Fix 2: Fix GHG_SCOPES missing closing brace
content = '\n'.join(lines)
content = content.replace(
    """GHG_SCOPES = {
    'scope1': 'Direct GHG emissions',
    'scope2': 'Indirect GHG emissions from purchased energy',
    'scope3': 'Other indirect GHG emissions'
# ESAP (European Single Access Point) Configuration""",
    """GHG_SCOPES = {
    'scope1': 'Direct GHG emissions',
    'scope2': 'Indirect GHG emissions from purchased energy',
    'scope3': 'Other indirect GHG emissions'
}

# ESAP (European Single Access Point) Configuration"""
)

# Fix 3: Fix ESAP_CONFIG missing 'report_types' key
content = content.replace(
    """ESAP_CONFIG = {
    'supported_languages': ['en', 'de', 'fr', 'es', 'it', 'nl', 'pl'],
        'E1': 'Climate_Change',""",
    """ESAP_CONFIG = {
    'supported_languages': ['en', 'de', 'fr', 'es', 'it', 'nl', 'pl'],
    'report_types': {
        'E1': 'Climate_Change',"""
)

# Fix 4: Add missing comma after 'pdf': '.pdf'
content = content.replace(
    """        'pdf': '.pdf'
    }
    'scope1': 'Direct emissions',""",
    """        'pdf': '.pdf'
    }
}

# Remove duplicate scope definitions"""
)

# Fix 5: Remove duplicate scope definitions
lines = content.split('\n')
cleaned_lines = []
skip_next = 0
for i, line in enumerate(lines):
    if skip_next > 0:
        skip_next -= 1
        continue
    if "'scope1': 'Direct emissions'," in line and i > 120:
        # Skip the duplicate scope definitions
        skip_next = 3
        continue
    cleaned_lines.append(line)

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write('\n'.join(cleaned_lines))

print("✅ Fixed all dictionary structure issues")
