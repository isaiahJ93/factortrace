#!/usr/bin/env python3
"""Fix unterminated triple-quoted strings"""

print("🔧 FIXING UNTERMINATED QUOTES...")

# Fix ghg_schemas.py
print("\n📋 Fixing ghg_schemas.py...")
with open('app/schemas/ghg_schemas.py', 'r') as f:
    lines = f.readlines()

# Check if line 65 has an unterminated docstring
if len(lines) > 64 and '"""' in lines[64] and not lines[64].count('"""') % 2 == 0:
    # Add closing quotes
    lines[64] = lines[64].rstrip() + '"""\n'
    with open('app/schemas/ghg_schemas.py', 'w') as f:
        f.writelines(lines)
    print("✅ Fixed line 65")

# Fix ghg_tables.py
print("\n📋 Fixing ghg_tables.py...")
with open('app/models/ghg_tables.py', 'r') as f:
    lines = f.readlines()

# Check if line 15 has an unterminated docstring
if len(lines) > 14 and '"""' in lines[14] and not lines[14].count('"""') % 2 == 0:
    # Add closing quotes
    lines[14] = lines[14].rstrip() + '"""\n'
    with open('app/models/ghg_tables.py', 'w') as f:
        f.writelines(lines)
    print("✅ Fixed line 15")

print("\n✅ All quotes fixed!")
print("🚀 Now run: uvicorn app.main:app --reload --port 8000")