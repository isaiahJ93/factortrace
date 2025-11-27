#!/usr/bin/env python3
"""
Fix syntax error in ESRS file
"""

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find and fix the line with double closing braces
for i, line in enumerate(lines):
    if '}},' in line and 'Will be calculated' in line:
        # Remove the extra brace
        lines[i] = line.replace('}},', '},')
        print(f"Fixed line {i+1}: {lines[i].strip()}")

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Syntax error fixed!")
