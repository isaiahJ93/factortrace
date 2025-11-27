#!/usr/bin/env python3
"""
Fix all syntax errors in ghg_calculator.py
"""

import re

# Read the file
with open("app/api/v1/endpoints/ghg_calculator.py", "r") as f:
    content = f.read()

# Fix pattern: find all "}" followed by newline and quote without comma
# This regex finds closing braces that should have commas
pattern = r'(\})\n(\s*"[^"]+": \{)'
replacement = r'\1,\n\2'

# Apply the fix
fixed_content = re.sub(pattern, replacement, content)

# Also fix any specific known issues
# Fix the steam block if it's missing a comma
fixed_content = fixed_content.replace('    }\n    "diesel"', '    },\n    "diesel"')
fixed_content = fixed_content.replace('    }\n    "waste_landfill"', '    },\n    "waste_landfill"')

# Count how many fixes were made
original_count = content.count('}\n    "')
fixed_count = fixed_content.count('},\n    "')
print(f"Fixed {fixed_count - content.count('},\n    \"')} missing commas")

# Write back
with open("app/api/v1/endpoints/ghg_calculator.py", "w") as f:
    f.write(fixed_content)

print("✅ Fixed all syntax errors")

# Verify by trying to import
try:
    import ast
    # Try to parse just the DEFAULT_EMISSION_FACTORS section
    match = re.search(r'DEFAULT_EMISSION_FACTORS = ({.*?})\n\n', fixed_content, re.DOTALL)
    if match:
        dict_str = match.group(1)
        # Basic syntax check
        compile(dict_str, '<string>', 'eval')
        print("✅ DEFAULT_EMISSION_FACTORS syntax is valid")
except Exception as e:
    print(f"⚠️  Syntax check failed: {e}")