#!/usr/bin/env python3
"""
Fix indentation in ghg_calculator.py
"""

# Read the file
with open("app/api/v1/endpoints/ghg_calculator.py", "r") as f:
    content = f.read()

# Fix common indentation issues in DEFAULT_EMISSION_FACTORS
import re

# Find the DEFAULT_EMISSION_FACTORS section
pattern = r'(DEFAULT_EMISSION_FACTORS = \{)(.*?)(\n\})'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Get the content inside the dictionary
    dict_content = match.group(2)
    
    # Fix indentation - ensure all top-level keys have 4 spaces
    lines = dict_content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if line.strip() and not line.strip().startswith('"'):
            # This is likely inside a nested dict, keep as is
            fixed_lines.append(line)
        elif line.strip().startswith('"') and '": {' in line:
            # This is a top-level key, ensure 4 spaces
            fixed_lines.append('    ' + line.strip())
        else:
            fixed_lines.append(line)
    
    # Reconstruct
    fixed_dict = '\n'.join(fixed_lines)
    fixed_content = match.group(1) + fixed_dict + match.group(3)
    
    # Replace in original content
    content = content[:match.start()] + fixed_content + content[match.end():]

# Write back
with open("app/api/v1/endpoints/ghg_calculator.py", "w") as f:
    f.write(content)

print("✅ Fixed indentation issues")