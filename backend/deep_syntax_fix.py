#!/usr/bin/env python3
"""
Deep syntax fix for esrs_e1_full.py
Handles multiple cascading syntax errors
"""

import re
import os
from datetime import datetime
import ast

def deep_syntax_fix():
    """Comprehensive fix for all syntax errors"""
    file_path = "app/api/v1/endpoints/esrs_e1_full.py"
    
    # Backup first
    backup_path = f"{file_path}.backup_deep_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Create backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✅ Backup created: {backup_path}")
        
        # Fix 1: Handle the IndentationError at line 4308
        if len(lines) > 4307:
            # Check line 4307 for an if statement
            if 'if' in lines[4306] and ':' in lines[4306]:
                # Line 4308 needs indentation
                if lines[4307].strip() and not lines[4307].startswith((' ', '\t')):
                    lines[4307] = '    ' + lines[4307]
                    print("✅ Fixed indentation at line 4308")
        
        # Fix 2: Find and fix all orphaned ") -> ET.Element:" lines
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for orphaned function signature endings
            if line == ") -> ET.Element:" or line == ") -> ET.Element":
                print(f"❌ Found orphaned line at {i+1}: '{line}'")
                
                # Look backwards for the function definition
                found_func = False
                for j in range(i-1, max(0, i-50), -1):
                    if 'def create_enhanced_xbrl_tag' in lines[j]:
                        print(f"   Found function at line {j+1}")
                        found_func = True
                        
                        # Check if function needs this ending
                        func_complete = False
                        for k in range(j, i):
                            if lines[k].rstrip().endswith(':'):
                                func_complete = True
                                break
                        
                        if func_complete:
                            # Function is already complete, remove orphaned line
                            lines.pop(i)
                            print(f"   Removed orphaned line")
                            i -= 1
                        else:
                            # Function needs completion - but it's orphaned, so remove
                            lines.pop(i)
                            print(f"   Removed orphaned line (function malformed)")
                            i -= 1
                        break
                
                if not found_func:
                    # No associated function, remove the line
                    lines.pop(i)
                    print(f"   Removed unassociated orphaned line")
                    i -= 1
            
            i += 1
        
        # Fix 3: Find and fix unclosed parentheses
        print("\n🔍 Checking for unclosed parentheses...")
        
        # Track parentheses in function definitions
        in_function = False
        func_start_line = -1
        paren_count = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for function definition start
            if line.strip().startswith('def ') and 'create_enhanced_xbrl_tag' in line:
                in_function = True
                func_start_line = i
                paren_count = 0
                print(f"\n📍 Found create_enhanced_xbrl_tag at line {i+1}")
            
            if in_function:
                # Count parentheses
                paren_count += line.count('(') - line.count(')')
                
                # Check if function signature should be complete
                if ':' in line and line.rstrip().endswith(':'):
                    if paren_count > 0:
                        # Missing closing parenthesis
                        print(f"   ❌ Unclosed parenthesis in function signature")
                        # Add closing parenthesis before the colon
                        line_fixed = line.rstrip()[:-1] + ') -> ET.Element:\n'
                        lines[i] = line_fixed
                        print(f"   ✅ Fixed: added closing parenthesis")
                        paren_count = 0
                    in_function = False
                elif paren_count == 0 and i > func_start_line:
                    # Parentheses are balanced but no closing colon
                    if not line.strip() and i + 1 < len(lines):
                        # Empty line, check next line
                        next_line = lines[i + 1].strip()
                        if next_line and not next_line.startswith('def ') and not next_line.startswith('@'):
                            # Function signature incomplete, add ending
                            lines[i] = ') -> ET.Element:\n'
                            print(f"   ✅ Added function ending at line {i+1}")
                            in_function = False
                    elif not line.rstrip().endswith(':'):
                        # Add the return type and colon
                        lines[i] = line.rstrip() + ' -> ET.Element:\n'
                        print(f"   ✅ Completed function signature at line {i+1}")
                        in_function = False
            
            i += 1
        
        # Fix 4: Remove any duplicate create_enhanced_xbrl_tag definitions
        print("\n🔍 Checking for duplicate function definitions...")
        
        content = ''.join(lines)
        func_pattern = r'def create_enhanced_xbrl_tag\s*\([^)]*\)[^:]*:.*?(?=\ndef\s|\nclass\s|\n@|\Z)'
        matches = list(re.finditer(func_pattern, content, re.DOTALL))
        
        if len(matches) > 1:
            print(f"❌ Found {len(matches)} definitions of create_enhanced_xbrl_tag")
            # Keep only the first valid one
            for i in range(len(matches) - 1, 0, -1):
                start = matches[i].start()
                end = matches[i].end()
                content = content[:start] + content[end:]
                print(f"   Removed duplicate definition #{i+1}")
            lines = content.splitlines(True)
        
        # Fix 5: Ensure proper structure around line 8338
        if len(lines) > 8337:
            print(f"\n🔍 Checking line 8338 area...")
            # Show context
            for i in range(max(0, 8335), min(len(lines), 8340)):
                print(f"   {i+1}: {lines[i].rstrip()}")
            
            # If there's an unclosed function definition here
            if 'def create_enhanced_xbrl_tag(' in lines[8337]:
                # Make sure it has a proper ending
                found_end = False
                for j in range(8338, min(len(lines), 8350)):
                    if lines[j].rstrip().endswith(':'):
                        found_end = True
                        break
                
                if not found_end:
                    # Find where parameters end and add the signature ending
                    for j in range(8338, min(len(lines), 8360)):
                        if ')' in lines[j]:
                            # Found closing paren, make sure it has return type
                            if '-> ET.Element:' not in lines[j]:
                                lines[j] = lines[j].rstrip() + ' -> ET.Element:\n'
                                print(f"   ✅ Fixed function signature at line {j+1}")
                            break
        
        # Write the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("\n✅ Deep syntax fix complete!")
        
        # Verify compilation
        import py_compile
        try:
            py_compile.compile(file_path, doraise=True)
            print("✅ File now compiles successfully!")
            return True
        except py_compile.PyCompileError as e:
            print(f"⚠️ Still has compilation errors: {e}")
            # Show the specific error location
            if hasattr(e, 'msg') and 'line' in str(e):
                print("\n🔍 Error details:")
                error_match = re.search(r'line (\d+)', str(e))
                if error_match:
                    error_line = int(error_match.group(1))
                    show_error_context(lines, error_line)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_error_context(lines, error_line):
    """Show context around an error line"""
    start = max(0, error_line - 5)
    end = min(len(lines), error_line + 5)
    
    print(f"\n📍 Context around line {error_line}:")
    print("-" * 60)
    for i in range(start, end):
        if i == error_line - 1:
            print(f">>> {i+1:4d}: {lines[i].rstrip()} <<<ERROR HERE")
        else:
            print(f"    {i+1:4d}: {lines[i].rstrip()}")
    print("-" * 60)

def verify_function_structure():
    """Verify the create_enhanced_xbrl_tag function structure"""
    file_path = "app/api/v1/endpoints/esrs_e1_full.py"
    
    print("\n🔍 Verifying function structure...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all create_enhanced_xbrl_tag definitions
        pattern = r'def create_enhanced_xbrl_tag.*?(?=\ndef\s|\nclass\s|\n@|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        print(f"Found {len(matches)} definition(s)")
        
        for i, match in enumerate(matches):
            lines = match.split('\n')
            print(f"\nDefinition #{i+1}:")
            print(f"  First line: {lines[0]}")
            print(f"  Length: {len(lines)} lines")
            
            # Check structure
            has_return_type = '-> ET.Element' in match
            has_docstring = '"""' in match
            has_implementation = 'elem = ' in match or 'return' in match
            
            print(f"  Has return type: {'✅' if has_return_type else '❌'}")
            print(f"  Has docstring: {'✅' if has_docstring else '❌'}")
            print(f"  Has implementation: {'✅' if has_implementation else '❌'}")
            
    except Exception as e:
        print(f"❌ Error verifying: {e}")

if __name__ == "__main__":
    print("🔧 DEEP SYNTAX FIX")
    print("=" * 60)
    
    success = deep_syntax_fix()
    
    if success:
        verify_function_structure()
        print("\n✅ All syntax errors fixed!")
        print("\n📋 Next steps:")
        print("1. Run: python3 test_ixbrl_generation.py")
        print("2. Restart your FastAPI server")
    else:
        print("\n⚠️ Manual intervention may be needed")
        print("Consider restoring from a backup and applying fixes manually")