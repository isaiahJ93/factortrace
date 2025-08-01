with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find a good insertion point (after SECTOR_SPECIFIC_REQUIREMENTS)
insert_line = -1
for i, line in enumerate(lines):
    if 'SECTOR_SPECIFIC_REQUIREMENTS = {' in line:
        # Find the closing brace
        brace_count = 0
        for j in range(i, len(lines)):
            brace_count += lines[j].count('{') - lines[j].count('}')
            if brace_count == 0 and j > i:
                insert_line = j + 2
                break
        break

if insert_line == -1:
    # Alternative: find after Scope3Category enum
    for i, line in enumerate(lines):
        if 'class Scope3Category' in line:
            # Skip to end of enum
            for j in range(i, len(lines)):
                if j > i and lines[j].strip() and not lines[j].startswith(' '):
                    insert_line = j
                    break
            break

if insert_line == -1:
    insert_line = 200

# Add ESAP constants
esap_config = '''
# ESAP (European Single Access Point) Configuration
ESAP_FILE_NAMING_PATTERN = "{lei}_{year}_{period}_{report_type}_{language}_{version}"

ESAP_CONFIG = {
    'supported_languages': ['en', 'de', 'fr', 'es', 'it', 'nl', 'pl'],
    'report_types': {
        'E1': 'Climate_Change',
        'E2': 'Pollution',
        'E3': 'Water_Marine_Resources',
        'E4': 'Biodiversity_Ecosystems',
        'E5': 'Resource_Use_Circular_Economy'
    },
    'file_extensions': {
        'xhtml': '.xhtml',
        'xml': '.xml',
        'pdf': '.pdf'
    }
}

'''

lines.insert(insert_line, esap_config)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print(f"✅ Added ESAP constants at line {insert_line}")
