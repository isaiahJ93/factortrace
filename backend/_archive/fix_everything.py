#!/usr/bin/env python3
"""Fix all remaining issues in one go"""

import os
import re

print("🚀 FIXING EVERYTHING...")

# Fix 1: Remove poolclass from database.py
print("\n📋 Fix 1: Removing poolclass...")
with open('app/core/database.py', 'r') as f:
    content = f.read()
content = re.sub(r'.*poolclass=QueuePool.*\n', '', content)
with open('app/core/database.py', 'w') as f:
    f.write(content)

# Fix 2: Fix DATABASE_URL in session.py
print("📋 Fix 2: Fixing DATABASE_URL in session.py...")
try:
    with open('app/db/session.py', 'r') as f:
        content = f.read()
    content = content.replace('settings.DATABASE_URL', 'str(settings.database_url)')
    with open('app/db/session.py', 'w') as f:
        f.write(content)
except FileNotFoundError:
    print("   session.py not found, skipping...")

# Fix 3: Add Scope3Category import to ghg_tables.py
print("📋 Fix 3: Adding Scope3Category import...")
with open('app/models/ghg_tables.py', 'r') as f:
    lines = f.readlines()

# Find where to insert the import
insert_index = -1
for i, line in enumerate(lines):
    if 'from app.core.database import Base' in line:
        insert_index = i + 1
        break

if insert_index > 0 and not any('Scope3Category' in line for line in lines):
    lines.insert(insert_index, 'from app.schemas.ghg_schemas import Scope3Category, CalculationMethod\n')

with open('app/models/ghg_tables.py', 'w') as f:
    f.writelines(lines)

# Fix 4: Fix backend.app imports
print("📋 Fix 4: Fixing incorrect import paths...")
with open('app/models/__init__.py', 'r') as f:
    content = f.read()
content = content.replace('from backend.app.models', 'from app.models')
with open('app/models/__init__.py', 'w') as f:
    f.write(content)

# Fix 5: Find and fix all DATABASE_URL references
print("📋 Fix 5: Fixing all DATABASE_URL references...")
for root, dirs, files in os.walk('app'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                if 'settings.DATABASE_URL' in content:
                    print(f"   Fixing: {filepath}")
                    content = content.replace('settings.DATABASE_URL', 'str(settings.database_url)')
                    with open(filepath, 'w') as f:
                        f.write(content)
            except:
                pass

print("\n✅ ALL FIXES APPLIED!")
print("🚀 Now run: uvicorn app.main:app --reload --port 8000")