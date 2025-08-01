#!/usr/bin/env python3
"""Add missing AssuranceReadinessLevel enum"""

from enum import Enum

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Define the missing enum
enum_definition = '''from enum import Enum

# ESRS Assurance Readiness Levels
class AssuranceReadinessLevel(Enum):
    NOT_READY = "not_ready"
    PARTIALLY_READY = "partially_ready"
    READY = "ready"
    ASSURED = "assured"

'''

# Check if we need to add the enum import
needs_enum_import = True
for line in lines[:50]:  # Check first 50 lines
    if 'from enum import' in line:
        needs_enum_import = False
        break

# Find where to insert the enum definition
insert_pos = -1
for i, line in enumerate(lines):
    if 'SECTOR_SPECIFIC_REQUIREMENTS' in line:
        # Find the end of SECTOR_SPECIFIC_REQUIREMENTS
        for j in range(i, len(lines)):
            if lines[j].strip() == '}':
                insert_pos = j + 2  # After the closing brace and blank line
                break
        break

if insert_pos == -1:
    # Fallback: insert at line 150
    insert_pos = 150

# Insert the enum definition
if needs_enum_import:
    # Add both import and class
    lines.insert(insert_pos, enum_definition)
else:
    # Just add the class
    lines.insert(insert_pos, enum_definition.replace('from enum import Enum\n\n', ''))

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added AssuranceReadinessLevel enum")
