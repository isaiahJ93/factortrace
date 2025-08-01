#!/usr/bin/env python3
"""Fix all missing imports and constants in ESRS file"""

import re

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find where imports end
import_end_line = 0
for i, line in enumerate(lines):
    if line.strip() and not line.strip().startswith(('import ', 'from ', '#')) and i > 10:
        import_end_line = i
        break

print(f"Import section ends at line {import_end_line}")

# Check for missing imports
missing_imports = []

# Check current imports
current_imports = '\n'.join(lines[:import_end_line])

# Standard library imports that might be missing
if 'import uuid' not in current_imports:
    missing_imports.append('import uuid')

if 'import datetime' not in current_imports and 'from datetime import' not in current_imports:
    missing_imports.append('import datetime')

if 'import json' not in current_imports:
    missing_imports.append('import json')

if 'import re' not in current_imports:
    missing_imports.append('import re')

if 'from typing import' not in current_imports:
    missing_imports.append('from typing import Dict, List, Any, Optional, Tuple')

if 'from decimal import Decimal' not in current_imports:
    missing_imports.append('from decimal import Decimal')

# XML/XBRL related imports
if 'from lxml import etree' not in current_imports:
    missing_imports.append('from lxml import etree')

# Add missing imports
if missing_imports:
    print(f"\nAdding {len(missing_imports)} missing imports:")
    for imp in missing_imports:
        print(f"  - {imp}")
    
    # Insert imports at the beginning (after any file docstring)
    insert_pos = 0
    for i, line in enumerate(lines):
        if not line.strip().startswith('"""') and not line.strip().startswith('#'):
            insert_pos = i
            break
    
    # Add imports
    for imp in reversed(missing_imports):
        lines.insert(insert_pos, imp + '\n')

# Add SECTOR_SPECIFIC_REQUIREMENTS if missing
sector_const = '''
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

# Check if SECTOR_SPECIFIC_REQUIREMENTS exists
content = ''.join(lines)
if 'SECTOR_SPECIFIC_REQUIREMENTS' not in content:
    print("\nAdding SECTOR_SPECIFIC_REQUIREMENTS constant...")
    
    # Find where to insert (after imports)
    insert_line = import_end_line + len(missing_imports)
    lines.insert(insert_line, sector_const)

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("\n✅ Fixed imports and constants")
