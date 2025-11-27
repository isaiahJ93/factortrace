#!/usr/bin/env python3
"""
Fix the DEFAULT_EMISSION_FACTORS structure
"""

# Read the file
with open("app/api/v1/endpoints/ghg_calculator.py", "r") as f:
    lines = f.readlines()

# Find and fix the issue around line 111
fixed_lines = []
skip_next = False

for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
        
    # Check if this is the problematic line 111
    if i == 110 and line.strip() == '},':
        # This is likely an extra closing brace, skip it
        print(f"Removing extra closing brace at line {i+1}")
        continue
    
    fixed_lines.append(line)

# Write back
with open("app/api/v1/endpoints/ghg_calculator.py", "w") as f:
    f.writelines(fixed_lines)

print("✅ Fixed structure")