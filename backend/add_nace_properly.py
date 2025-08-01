#!/usr/bin/env python3

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find a good place to insert - after imports but before first function
insert_index = -1
for i, line in enumerate(lines):
    if line.startswith('router = APIRouter'):
        insert_index = i
        break
    elif line.startswith('logger = '):
        insert_index = i + 1
    elif line.startswith('# ==='):
        insert_index = i

if insert_index == -1:
    # Default to line 100 if we can't find a good spot
    insert_index = min(100, len(lines))

# Create NACE_CODE_REGISTRY
nace_registry = '''
# NACE Code Registry (European Statistical Classification of Economic Activities)
NACE_CODE_REGISTRY = {
    'A': 'Agriculture, forestry and fishing',
    'B': 'Mining and quarrying',
    'C': 'Manufacturing',
    'D': 'Electricity, gas, steam and air conditioning supply',
    'E': 'Water supply; sewerage, waste management',
    'F': 'Construction',
    'G': 'Wholesale and retail trade',
    'H': 'Transportation and storage',
    'I': 'Accommodation and food service activities',
    'J': 'Information and communication',
    'K': 'Financial and insurance activities',
    'L': 'Real estate activities',
    'M': 'Professional, scientific and technical activities',
    'N': 'Administrative and support service activities',
    'O': 'Public administration and defence',
    'P': 'Education',
    'Q': 'Human health and social work activities',
    'R': 'Arts, entertainment and recreation',
    'S': 'Other service activities',
    # Common specific codes
    'C.20': 'Manufacture of chemicals and chemical products',
    'C.24': 'Manufacture of basic metals',
    'D.35': 'Electricity, gas, steam and air conditioning supply',
    'G.47': 'Retail trade, except of motor vehicles',
    'J.62': 'Computer programming, consultancy and related activities',
    'K.64': 'Financial service activities',
    'M.70': 'Activities of head offices; management consultancy',
}

'''

# Insert it
lines.insert(insert_index, nace_registry)

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print(f"✅ Added NACE_CODE_REGISTRY at line {insert_index}")
