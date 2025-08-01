#!/usr/bin/env python3
"""Fix multiple issues in ESRS file"""

import re

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

fixes_applied = []

# Fix 1: Add SECTOR_SPECIFIC_REQUIREMENTS if missing
if 'SECTOR_SPECIFIC_REQUIREMENTS = {' not in content:
    print("Adding SECTOR_SPECIFIC_REQUIREMENTS...")
    
    # Add after imports (around line 50-100)
    lines = content.split('\n')
    insert_pos = 100
    
    sector_requirements = '''
# ESRS Sector-specific requirements
SECTOR_SPECIFIC_REQUIREMENTS = {
    'A': {'name': 'Agriculture, forestry and fishing', 'additional_disclosures': []},
    'B': {'name': 'Mining and quarrying', 'additional_disclosures': []},
    'C': {'name': 'Manufacturing', 'additional_disclosures': []},
    'D': {'name': 'Energy supply', 'additional_disclosures': []},
    'E': {'name': 'Water and waste', 'additional_disclosures': []},
    'F': {'name': 'Construction', 'additional_disclosures': []},
    'G': {'name': 'Trade', 'additional_disclosures': []},
    'H': {'name': 'Transportation', 'additional_disclosures': []},
    'I': {'name': 'Hospitality', 'additional_disclosures': []},
    'J': {'name': 'Information and communication', 'additional_disclosures': [
        'data_center_efficiency', 'renewable_energy_use', 'e_waste_management'
    ]},
    'K': {'name': 'Financial services', 'additional_disclosures': []},
    'L': {'name': 'Real estate', 'additional_disclosures': []},
    'M': {'name': 'Professional services', 'additional_disclosures': []},
    'N': {'name': 'Administrative services', 'additional_disclosures': []}
}
'''
    
    lines.insert(insert_pos, sector_requirements)
    content = '\n'.join(lines)
    fixes_applied.append("Added SECTOR_SPECIFIC_REQUIREMENTS")

# Fix 2: Fix datetime.now() calls
datetime_fixes = 0

# Pattern 1: datetime.now() -> datetime.datetime.now()
pattern1 = re.compile(r'\bdatetime\.now\(\)')
matches1 = pattern1.findall(content)
if matches1:
    content = pattern1.sub('datetime.datetime.now()', content)
    datetime_fixes += len(matches1)
    print(f"Fixed {len(matches1)} instances of datetime.now()")

if datetime_fixes > 0:
    fixes_applied.append(f"Fixed {datetime_fixes} datetime issues")

# Write the fixed content back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("\n✅ Fixes applied:")
for fix in fixes_applied:
    print(f"  - {fix}")
