#!/usr/bin/env python3
"""
Find and fix remaining hardcoded emission values in ESRS
"""

import re

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find all hardcoded emission values
pattern = r'"category_\d+"\s*:\s*{\s*"emissions_tco2e"\s*:\s*\d+\s*,\s*"excluded"\s*:\s*False'
matches = list(re.finditer(pattern, content))

print(f"Found {len(matches)} hardcoded emission values:")
for i, match in enumerate(matches):
    line_num = content[:match.start()].count('\n') + 1
    print(f"  Line {line_num}: {match.group()}")

# Replace all hardcoded values with placeholders
for match in reversed(matches):  # Reverse to maintain positions
    category_num = re.search(r'category_(\d+)', match.group()).group(1)
    replacement = f'"category_{category_num}": {{"emissions_tco2e": 0, "excluded": True, "note": "Will be calculated"}}'
    content = content[:match.start()] + replacement + content[match.end():]

# Save the fixed file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("\n✅ Fixed all hardcoded values!")