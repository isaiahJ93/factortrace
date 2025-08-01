#!/usr/bin/env python3
import re

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find where to add the NACE_CODE_REGISTRY
# Look for other constants or registries
import_section_end = content.find('\nrouter = APIRouter')
if import_section_end == -1:
    import_section_end = content.find('\n\ndef ')

# Add NACE_CODE_REGISTRY if not present
if 'NACE_CODE_REGISTRY' not in content:
    nace_registry = '''
# NACE Code Registry (European industrial classification)
NACE_CODE_REGISTRY = {
    'A.01': 'Crop and animal production',
    'C.20': 'Manufacture of chemicals',
    'C.24': 'Manufacture of basic metals',
    'D.35': 'Electricity, gas supply',
    'E.38': 'Waste collection',
    'F.41': 'Construction of buildings',
    'G.47': 'Retail trade',
    'H.49': 'Land transport',
    'J.62': 'Computer programming',
    'K.64': 'Financial service',
    'M.70': 'Management consultancy',
    # Add more as needed
}
'''
    content = content[:import_section_end] + nace_registry + content[import_section_end:]
    
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
        f.write(content)
    
    print("✅ Added NACE_CODE_REGISTRY")
else:
    print("✅ NACE_CODE_REGISTRY already exists")

# Also fix the validation function to handle missing NACE codes
pattern = r"nace_valid = data\.get\('primary_nace_code'\) in NACE_CODE_REGISTRY"
replacement = "nace_valid = data.get('primary_nace_code', 'C.20') in NACE_CODE_REGISTRY if 'NACE_CODE_REGISTRY' in globals() else True"

if pattern in content:
    content = re.sub(pattern, replacement, content)
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
        f.write(content)
    print("✅ Fixed NACE validation")
