#!/usr/bin/env python3
"""
Comprehensive fix for ghg_calculator.py structure
"""

import json
import re

# Read the file
with open("app/api/v1/endpoints/ghg_calculator.py", "r") as f:
    lines = f.readlines()

# Find where DEFAULT_EMISSION_FACTORS starts and ends
start_idx = None
end_idx = None
brace_count = 0

for i, line in enumerate(lines):
    if "DEFAULT_EMISSION_FACTORS = {" in line:
        start_idx = i
        brace_count = 1
    elif start_idx is not None:
        brace_count += line.count('{') - line.count('}')
        if brace_count == 0:
            end_idx = i
            break

if start_idx and end_idx:
    print(f"Found DEFAULT_EMISSION_FACTORS from line {start_idx+1} to {end_idx+1}")
    
    # Extract and fix the dictionary section
    dict_lines = lines[start_idx:end_idx+1]
    
    # Fix indentation and structure
    fixed_lines = []
    fixed_lines.append(dict_lines[0])  # Keep the "DEFAULT_EMISSION_FACTORS = {" line
    
    current_indent = 4
    for i, line in enumerate(dict_lines[1:-1], 1):
        stripped = line.strip()
        
        if not stripped:
            fixed_lines.append("\n")
            continue
            
        # Determine proper indentation
        if stripped.endswith(": {"):
            # This is a main key
            fixed_lines.append(" " * 4 + stripped + "\n")
            current_indent = 8
        elif stripped == "},":
            # End of inner dict with comma
            fixed_lines.append(" " * 4 + stripped + "\n")
            current_indent = 4
        elif stripped == "}":
            # End of inner dict without comma - add it
            fixed_lines.append(" " * 4 + "}," + "\n")
            current_indent = 4
        elif current_indent == 8:
            # Inside inner dict
            fixed_lines.append(" " * 8 + stripped + "\n")
    
    fixed_lines.append(dict_lines[-1])  # Keep the closing "}"
    
    # Rebuild the file
    new_lines = lines[:start_idx] + fixed_lines + lines[end_idx+1:]
    
    # Write back
    with open("app/api/v1/endpoints/ghg_calculator.py", "w") as f:
        f.writelines(new_lines)
    
    print("✅ Fixed DEFAULT_EMISSION_FACTORS structure")
else:
    print("❌ Could not find DEFAULT_EMISSION_FACTORS")

# Do the same for CATEGORY_3_FACTORS
with open("app/api/v1/endpoints/ghg_calculator.py", "r") as f:
    lines = f.readlines()

start_idx = None
end_idx = None
brace_count = 0

for i, line in enumerate(lines):
    if "CATEGORY_3_FACTORS = {" in line:
        start_idx = i
        brace_count = 1
    elif start_idx is not None:
        brace_count += line.count('{') - line.count('}')
        if brace_count == 0:
            end_idx = i
            break

if start_idx and end_idx:
    print(f"Found CATEGORY_3_FACTORS from line {start_idx+1} to {end_idx+1}")
    
    # Extract and fix
    dict_lines = lines[start_idx:end_idx+1]
    fixed_lines = []
    fixed_lines.append(dict_lines[0])
    
    current_indent = 4
    for line in dict_lines[1:-1]:
        stripped = line.strip()
        if not stripped:
            fixed_lines.append("\n")
            continue
            
        if stripped.endswith(": {"):
            fixed_lines.append(" " * 4 + stripped + "\n")
            current_indent = 8
        elif stripped in ["}", "},"]:
            fixed_lines.append(" " * 4 + "}," + "\n")
            current_indent = 4
        else:
            fixed_lines.append(" " * current_indent + stripped + "\n")
    
    fixed_lines.append(dict_lines[-1])
    
    # Rebuild
    new_lines = lines[:start_idx] + fixed_lines + lines[end_idx+1:]
    
    with open("app/api/v1/endpoints/ghg_calculator.py", "w") as f:
        f.writelines(new_lines)
    
    print("✅ Fixed CATEGORY_3_FACTORS structure")

print("\n✅ All structural fixes applied")
print("Now testing import...")

try:
    from app.api.v1.endpoints.ghg_calculator import DEFAULT_EMISSION_FACTORS, CATEGORY_3_FACTORS
    print("✅ Successfully imported emission factors!")
    print(f"   - DEFAULT_EMISSION_FACTORS has {len(DEFAULT_EMISSION_FACTORS)} entries")
    print(f"   - CATEGORY_3_FACTORS has {len(CATEGORY_3_FACTORS)} entries")
except Exception as e:
    print(f"❌ Import failed: {e}")