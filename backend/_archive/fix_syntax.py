#!/usr/bin/env python3
"""
Emergency repair script for corrupted Python string literals.
Fixes both ghg_tables.py and ghg_schemas.py in one shot.
"""

import re
import os

def fix_ghg_tables():
    """Fix the corrupted docstring in ghg_tables.py"""
    filepath = 'app/models/ghg_tables.py'
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find the GHGOrganization class and fix the mangled docstring
    # Pattern matches the class definition with corrupted quotes
    pattern = r'(class GHGOrganization\(Base\):\s*\n\s*)""".*?""".*?\n.*?__tablename__'
    
    # Replace with clean version
    replacement = r'\1"""Renamed to avoid conflict with existing Organization model"""\n    __tablename__'
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Also ensure line 16 is clean - remove any leading quotes before __tablename__
    content = re.sub(r'\n\s*"{2,}\s*__tablename__', r'\n    __tablename__', content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {filepath}")

def fix_ghg_schemas():
    """Fix any unterminated strings in ghg_schemas.py"""
    filepath = 'app/schemas/ghg_schemas.py'
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Check for common issues around line 65
    fixed = False
    for i in range(len(lines)):
        line = lines[i]
        
        # Count triple quotes in the line
        triple_count = line.count('"""')
        
        # If odd number of triple quotes, we have an unterminated string
        if triple_count % 2 == 1:
            # Check if this is a docstring that should be on one line
            if i < len(lines) - 1 and 'class' in lines[i-1] or 'def' in lines[i-1]:
                # Look for the closing quotes on subsequent lines
                for j in range(i+1, min(i+10, len(lines))):
                    if '"""' in lines[j]:
                        # Merge the docstring onto one line
                        docstring_content = ''.join(lines[i:j+1]).strip()
                        # Extract just the text between quotes
                        match = re.search(r'"""(.*?)"""', docstring_content, re.DOTALL)
                        if match:
                            clean_text = match.group(1).strip().replace('\n', ' ')
                            lines[i] = f'    """{clean_text}"""\n'
                            # Clear the subsequent lines
                            for k in range(i+1, j+1):
                                lines[k] = ''
                            fixed = True
                            break
    
    # Additional check: ensure all docstrings are properly terminated
    content = ''.join(lines)
    
    # Fix any standalone unterminated docstrings
    content = re.sub(r'"""([^"]*?)\n\s*"""', r'"""\1"""', content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {filepath}")

def verify_syntax():
    """Verify both files compile without syntax errors"""
    import ast
    
    files = ['app/models/ghg_tables.py', 'app/schemas/ghg_schemas.py']
    
    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            ast.parse(content)
            print(f"✅ {filepath} - Syntax OK")
        except SyntaxError as e:
            print(f"❌ {filepath} - Still has syntax error at line {e.lineno}: {e.msg}")
            # Show the problematic lines
            with open(filepath, 'r') as f:
                lines = f.readlines()
            start = max(0, e.lineno - 3)
            end = min(len(lines), e.lineno + 2)
            print("Context:")
            for i in range(start, end):
                marker = ">>>" if i == e.lineno - 1 else "   "
                print(f"{marker} {i+1}: {lines[i]}", end='')

if __name__ == "__main__":
    print("🔧 Emergency String Literal Repair Script")
    print("=" * 50)
    
    # Fix both files
    fix_ghg_tables()
    fix_ghg_schemas()
    
    print("\n📋 Verifying syntax...")
    verify_syntax()
    
    print("\n🚀 Ready to start server with:")
    print("   uvicorn app.main:app --reload --port 8000")
