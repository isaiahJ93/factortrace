#!/usr/bin/env python3

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find where to add constants (after imports, before router)
insert_index = -1
for i, line in enumerate(lines):
    if 'router = APIRouter' in line:
        insert_index = i
        break

if insert_index == -1:
    insert_index = 50  # Default position

# Add all missing constants
missing_constants = '''
# NACE Code Registry (European Statistical Classification)
NACE_CODE_REGISTRY = {
    'A': 'Agriculture, forestry and fishing',
    'B': 'Mining and quarrying',
    'C': 'Manufacturing',
    'C.20': 'Manufacture of chemicals',
    'D': 'Electricity, gas, steam',
    'E': 'Water supply; sewerage',
    'F': 'Construction',
    'G': 'Wholesale and retail trade',
    'G.47': 'Retail trade',
    'H': 'Transportation and storage',
    'I': 'Accommodation and food',
    'J': 'Information and communication',
    'J.62': 'Computer programming',
    'K': 'Financial and insurance',
    'L': 'Real estate',
    'M': 'Professional, scientific',
    'N': 'Administrative support',
    'O': 'Public administration',
    'P': 'Education',
    'Q': 'Human health',
    'R': 'Arts, entertainment',
    'S': 'Other service activities',
}

# ESAP Configuration
ESAP_CONFIG = {
    'enabled': True,
    'api_endpoint': 'https://api.esap.europa.eu/v1',
    'submission_format': 'iXBRL',
    'validation_level': 'ESRS_E1',
}

# Climate Risk Categories
CLIMATE_RISK_CATEGORIES = {
    'physical': ['acute', 'chronic'],
    'transition': ['policy', 'technology', 'market', 'reputation'],
}

# GHG Protocol Scopes
GHG_SCOPES = {
    'scope1': 'Direct emissions',
    'scope2': 'Indirect emissions from energy',
    'scope3': 'Other indirect emissions',
}

'''

# Insert the constants
lines.insert(insert_index, missing_constants)

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added missing constants to esrs_e1_full.py")
