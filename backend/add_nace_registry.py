#!/usr/bin/env python3

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Check if NACE_CODE_REGISTRY exists
if 'NACE_CODE_REGISTRY' not in content:
    # Find a good place to insert (after imports, before router)
    import_end = content.find('\nrouter = APIRouter')
    if import_end == -1:
        import_end = content.find('\ndef ')
    
    # Add NACE registry
    nace_code = '''
# NACE Code Registry for ESRS compliance
NACE_CODE_REGISTRY = {
    'A': 'Agriculture, forestry and fishing',
    'B': 'Mining and quarrying', 
    'C': 'Manufacturing',
    'D': 'Electricity, gas, steam',
    'E': 'Water supply; sewerage',
    'F': 'Construction',
    'G': 'Wholesale and retail trade',
    'H': 'Transportation and storage',
    'I': 'Accommodation and food service',
    'J': 'Information and communication',
    'K': 'Financial and insurance',
    'L': 'Real estate activities',
    'M': 'Professional, scientific',
    'N': 'Administrative and support',
    'O': 'Public administration',
    'P': 'Education',
    'Q': 'Human health and social work',
    'R': 'Arts, entertainment',
    'S': 'Other service activities',
    # Add specific codes
    'C.20': 'Manufacture of chemicals',
    'G.47': 'Retail trade',
    'J.62': 'Computer programming',
}
'''
    
    content = content[:import_end] + nace_code + content[import_end:]
    
    # Save the file
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
        f.write(content)
    
    print("✅ Added NACE_CODE_REGISTRY")
else:
    print("✅ NACE_CODE_REGISTRY already exists")
