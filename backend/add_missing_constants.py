#!/usr/bin/env python3
"""Add all missing constants to ESRS file"""

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Only add if not already present
if 'ESAP_FILE_NAMING_PATTERN' not in content:
    # Find a good insertion point
    lines = content.split('\n')
    insert_line = 250  # Default
    
    # Look for existing constants section
    for i, line in enumerate(lines):
        if 'SECTOR_SPECIFIC_REQUIREMENTS' in line:
            for j in range(i, min(i+100, len(lines))):
                if lines[j].strip() == '}' and j > i:
                    insert_line = j + 2
                    break
            break
    
    # Constants to add
    constants = '''
# ESAP (European Single Access Point) Configuration
ESAP_FILE_NAMING_PATTERN = "{lei}_{year}_{period}_{report_type}_{language}_{version}"

ESAP_CONFIG = {
    'supported_languages': ['en', 'de', 'fr', 'es', 'it', 'nl', 'pl'],
    'report_types': {
        'E1': 'Climate_Change'
    }
}

# GLEIF API Configuration
GLEIF_API_CONFIG = {
    'base_url': 'https://api.gleif.org/api/v1',
    'timeout': 30
}

# EU Taxonomy DNSH Criteria
EU_TAXONOMY_DNSH_CRITERIA = {}

# Emission Factor Registry
EMISSION_FACTOR_REGISTRY = {}

# Blockchain Configuration
BLOCKCHAIN_CONFIG = {'enabled': False}

'''
    
    lines.insert(insert_line, constants)
    
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
        f.write('\n'.join(lines))
    
    print("✅ Added missing constants")
else:
    print("Constants already present")
