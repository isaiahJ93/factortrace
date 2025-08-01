with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find the right place to insert constants - after imports, before first class/function
insert_pos = -1
for i, line in enumerate(lines):
    # Skip past imports
    if i < 50:
        continue
    # Find first non-import, non-comment, non-empty line that's not indented
    if line.strip() and not line.startswith(' ') and not line.startswith('#'):
        if 'class ' in line or 'def ' in line:
            insert_pos = i
            break

if insert_pos == -1:
    # Look for NACE_CODE_REGISTRY or similar constants
    for i, line in enumerate(lines):
        if 'NACE_CODE_REGISTRY' in line:
            insert_pos = i
            break

if insert_pos == -1:
    insert_pos = 50  # Default after imports

# Add constants
constants = '''
# ESAP (European Single Access Point) Configuration
ESAP_FILE_NAMING_PATTERN = "{lei}_{year}_{period}_{report_type}_{language}_{version}"

ESAP_CONFIG = {
    'supported_languages': ['en', 'de', 'fr', 'es', 'it', 'nl', 'pl'],
    'report_types': {
        'E1': 'Climate_Change'
    }
}

'''

# Only add if not already present
content = ''.join(lines)
if 'ESAP_FILE_NAMING_PATTERN' not in content:
    lines.insert(insert_pos, constants)
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
        f.writelines(lines)
    print(f"✅ Added ESAP constants at line {insert_pos}")
else:
    print("ESAP constants already present")
