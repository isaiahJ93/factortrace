#!/usr/bin/env python3
import re

# Read the file
with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Find the incorrect import statement
# Body should be imported from fastapi, not from app.api.v1.endpoints
content = re.sub(
    r'from app\.api\.v1\.endpoints import \((.*?), Body\)',
    r'from app.api.v1.endpoints import (\1)',
    content,
    flags=re.DOTALL
)

# Add Body to the fastapi imports if not already there
if 'from fastapi import' in content:
    # Check if Body is already imported
    if 'Body' not in content:
        # Add Body to existing fastapi import
        content = re.sub(
            r'from fastapi import ([^)]+)',
            lambda m: f"from fastapi import {m.group(1)}, Body" if 'Body' not in m.group(1) else m.group(0),
            content
        )
else:
    # Add new fastapi import
    import_section = content.find('from app')
    if import_section > 0:
        content = content[:import_section] + 'from fastapi import APIRouter, Body\n' + content[import_section:]

# Save the fixed file
with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("✅ Fixed Body import")

# Check the imports
lines = content.split('\n')
print("\nImport statements:")
for i, line in enumerate(lines[:50]):
    if 'import' in line and ('Body' in line or 'fastapi' in line):
        print(f"  Line {i+1}: {line.strip()}")
