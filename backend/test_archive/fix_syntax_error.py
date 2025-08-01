#!/usr/bin/env python3
"""
Emergency fix for syntax error in esrs_e1_full.py
Fixes the unmatched parenthesis at line 4840
"""

import re
import os
from datetime import datetime

def fix_syntax_error():
    """Fix the syntax error at line 4840"""
    file_path = "app/api/v1/endpoints/esrs_e1_full.py"
    
    # Backup first
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Create backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✅ Backup created: {backup_path}")
        
        # Find and fix the syntax error around line 4840
        # Look for the unmatched parenthesis pattern
        for i in range(max(0, 4835), min(len(lines), 4845)):
            if i < len(lines):
                line = lines[i]
                # Check for standalone ) -> ET.Element:
                if line.strip() == ") -> ET.Element:":
                    print(f"❌ Found syntax error at line {i+1}: '{line.strip()}'")
                    
                    # Look backwards for the function definition
                    for j in range(i-1, max(0, i-50), -1):
                        if 'def create_enhanced_xbrl_tag' in lines[j]:
                            print(f"📍 Found function definition at line {j+1}")
                            
                            # Check if there's already a proper signature
                            func_start = j
                            func_lines = []
                            k = j
                            while k < len(lines) and not lines[k].strip().endswith(':'):
                                func_lines.append(lines[k])
                                k += 1
                            
                            # If we found the problematic line, fix it
                            if k < len(lines) and lines[k].strip() == ") -> ET.Element:":
                                # Remove the orphaned line
                                lines.pop(k)
                                print(f"✅ Removed orphaned line at {k+1}")
                                
                                # Ensure the function has a proper signature
                                if not any('-> ET.Element:' in line for line in func_lines):
                                    # Add proper return type to the last parameter line
                                    last_param_idx = func_start + len(func_lines) - 1
                                    lines[last_param_idx] = lines[last_param_idx].rstrip() + " -> ET.Element:\n"
                                    print(f"✅ Fixed function signature")
                            break
        
        # Write the fixed file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Syntax error fixed!")
        
        # Verify it's fixed by trying to compile
        import py_compile
        try:
            py_compile.compile(file_path, doraise=True)
            print("✅ File now compiles successfully!")
        except py_compile.PyCompileError as e:
            print(f"⚠️ Still has compilation errors: {e}")
            
    except Exception as e:
        print(f"❌ Error fixing syntax: {e}")
        # Restore backup if something went wrong
        if os.path.exists(backup_path):
            import shutil
            shutil.move(backup_path, file_path)
            print("🔄 Restored backup due to error")

if __name__ == "__main__":
    print("🔧 EMERGENCY SYNTAX FIX")
    print("=" * 50)
    fix_syntax_error()