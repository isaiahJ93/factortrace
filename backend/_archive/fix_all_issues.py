#!/usr/bin/env python3
"""Fix all remaining issues"""

print("🚀 FIXING ALL ISSUES...")

# Fix 1: Database.py indentation
print("\n📋 Fixing database.py indentation...")
with open('app/core/database.py', 'r') as f:
    lines = f.readlines()

fixed_lines = []
inside_function = False
for i, line in enumerate(lines):
    # Look for create_engine block
    if 'create_engine(' in line:
        inside_function = True
        fixed_lines.append(line)
    elif inside_function:
        # If line has content and no indentation, add it
        if line.strip() and not line[0].isspace() and ')' not in line:
            fixed_lines.append('    ' + line)
        else:
            fixed_lines.append(line)
        if ')' in line and not line.strip().endswith(','):
            inside_function = False
    else:
        fixed_lines.append(line)

with open('app/core/database.py', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Fixed database.py indentation")

# Fix 2: Scope3Category import in ghg_schemas.py
print("\n📋 Fixing Scope3Category import...")
with open('app/schemas/ghg_schemas.py', 'r') as f:
    content = f.read()

# Replace wrong import paths
content = content.replace('from app.models.ghg_protocol_models import Scope3Category', 
                         'from app.models.enums import Scope3Category')
content = content.replace('from models.enums import Scope3Category',
                         'from app.models.enums import Scope3Category')

# Remove duplicate lines
lines = content.split('\n')
seen = set()
unique_lines = []
for line in lines:
    if line not in seen or not line.strip():
        seen.add(line)
        unique_lines.append(line)

with open('app/schemas/ghg_schemas.py', 'w') as f:
    f.write('\n'.join(unique_lines))

print("✅ Fixed Scope3Category import")

# Fix 3: Check other potential issues
print("\n📋 Checking for other issues...")

# Ensure ghg_tables.py also uses correct import
try:
    with open('app/models/ghg_tables.py', 'r') as f:
        content = f.read()
    
    if 'from app.schemas.ghg_schemas import Scope3Category' in content:
        # This is correct, no change needed
        print("✅ ghg_tables.py imports look correct")
except:
    pass

print("\n✅ ALL FIXES APPLIED!")
print("\n🚀 Now run: uvicorn app.main:app --reload --port 8000")