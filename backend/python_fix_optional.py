#!/usr/bin/env python3
"""Fix all Optional import issues in the codebase"""

import os
import re

def fix_optional_imports(filepath):
    """Fix Optional imports in a Python file"""
    print(f"Fixing {filepath}...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Check if Optional is used in the file
    content = ''.join(lines)
    if 'Optional' not in content:
        print(f"  ✓ No Optional usage found")
        return False
    
    # Check if Optional is already imported
    has_optional_import = any('from typing import' in line and 'Optional' in line for line in lines)
    if has_optional_import:
        print(f"  ✓ Optional already imported")
        return False
    
    # Find existing typing import
    typing_import_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('from typing import'):
            typing_import_idx = i
            break
    
    if typing_import_idx is not None:
        # Add Optional to existing import
        current_line = lines[typing_import_idx].rstrip()
        if current_line.endswith(','):
            new_line = current_line + ' Optional\n'
        else:
            # Extract the imports
            match = re.match(r'from typing import (.+)', current_line)
            if match:
                imports = match.group(1)
                new_line = f'from typing import {imports}, Optional\n'
            else:
                new_line = current_line  # Shouldn't happen
        lines[typing_import_idx] = new_line
        print(f"  ✓ Added Optional to existing typing import on line {typing_import_idx + 1}")
    else:
        # Add new typing import after docstring or at top
        insert_idx = 0
        in_docstring = False
        for i, line in enumerate(lines):
            if i == 0 and line.strip().startswith('"""'):
                in_docstring = True
                continue
            if in_docstring and line.strip().endswith('"""'):
                insert_idx = i + 1
                break
            if not in_docstring and line.strip() and not line.strip().startswith('#'):
                insert_idx = i
                break
        
        lines.insert(insert_idx, 'from typing import Optional\n')
        print(f"  ✓ Added new typing import at line {insert_idx + 1}")
    
    # Write back
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    return True

# Priority files to fix
priority_files = [
    'app/schemas/ghg_schemas.py',
    'app/models/ghg_tables.py',
    'app/services/reporting_service.py'
]

print("🔧 Python Optional Import Fixer")
print("==============================\n")

# Fix priority files first
for filepath in priority_files:
    if os.path.exists(filepath):
        fix_optional_imports(filepath)
    else:
        print(f"❌ {filepath} not found")

# Fix all other Python files
print("\n📋 Scanning all Python files...")
for root, dirs, files in os.walk('app'):
    # Skip __pycache__
    dirs[:] = [d for d in dirs if d != '__pycache__']
    
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            if filepath not in priority_files:
                if fix_optional_imports(filepath):
                    print(f"  ✓ Fixed {filepath}")

print("\n✅ All Optional imports fixed!")
print("\n🚀 Run this to start the server:")
print("   uvicorn app.main:app --reload --port 8000")