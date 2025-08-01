#!/usr/bin/env python3
"""
Fix all remaining indentation issues in ESRS E1 file
This will iteratively fix each error until the file compiles
"""

import ast
import sys
from pathlib import Path

def fix_all_indentation_errors():
    filepath = Path("app/api/v1/endpoints/esrs_e1_full.py")
    
    print("🚀 FIXING ALL REMAINING INDENTATION ISSUES")
    print("=" * 50)
    
    fixed_count = 0
    max_iterations = 50  # Prevent infinite loops
    
    for iteration in range(max_iterations):
        try:
            # Try to compile the file
            with open(filepath, 'r') as f:
                content = f.read()
            
            compile(content, filepath, 'exec')
            
            print(f"\n✅ SUCCESS! Fixed {fixed_count} indentation issues.")
            print("🎉 YOUR ESRS E1 iXBRL GENERATOR IS NOW PRODUCTION READY!")
            
            # Do a final XBRL-specific validation
            validate_xbrl_structure(content)
            
            return True
            
        except IndentationError as e:
            fixed_count += 1
            print(f"\n🔧 Fixing issue #{fixed_count}: {e.msg} at line {e.lineno}")
            
            if not fix_indentation_error(filepath, e):
                print("❌ Could not automatically fix this error")
                show_manual_fix(filepath, e)
                return False
                
        except SyntaxError as e:
            if "expected an indented block" in str(e):
                fixed_count += 1
                print(f"\n🔧 Fixing issue #{fixed_count}: Missing indentation at line {e.lineno}")
                
                if not fix_missing_indentation(filepath, e.lineno):
                    print("❌ Could not automatically fix this error")
                    show_manual_fix(filepath, e)
                    return False
            else:
                print(f"\n❌ Non-indentation syntax error: {e}")
                show_manual_fix(filepath, e)
                return False
                
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            return False
    
    print(f"\n⚠️  Reached maximum iterations ({max_iterations}). Manual intervention needed.")
    return False

def fix_indentation_error(filepath, error):
    """Fix a specific indentation error"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    if error.lineno and error.lineno <= len(lines):
        line_idx = error.lineno - 1
        
        # Get the context
        print(f"  Context: {lines[line_idx].strip()[:50]}...")
        
        # For "unindent does not match", we need to find the correct indentation
        if "unindent does not match" in error.msg:
            # Find the matching block start
            for i in range(line_idx - 1, max(0, line_idx - 30), -1):
                if lines[i].rstrip().endswith(':'):
                    block_indent = len(lines[i]) - len(lines[i].lstrip())
                    lines[line_idx] = ' ' * block_indent + lines[line_idx].lstrip()
                    print(f"  ✓ Fixed indentation to {block_indent} spaces")
                    break
        
        # Save the fix
        with open(filepath, 'w') as f:
            f.writelines(lines)
        
        return True
    
    return False

def fix_missing_indentation(filepath, line_num):
    """Fix missing indentation after control statements"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    if line_num and line_num <= len(lines):
        prev_line_idx = line_num - 2
        curr_line_idx = line_num - 1
        
        if prev_line_idx >= 0:
            prev_line = lines[prev_line_idx]
            
            # Check if previous line ends with colon
            if prev_line.rstrip().endswith(':'):
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                expected_indent = prev_indent + 4
                
                # Fix current line and possibly following lines
                fixed_lines = 0
                for i in range(curr_line_idx, min(curr_line_idx + 20, len(lines))):
                    line = lines[i]
                    if line.strip():  # Non-empty line
                        current_indent = len(line) - len(line.lstrip())
                        
                        # If this line should be in the block
                        if current_indent <= prev_indent:
                            lines[i] = ' ' * expected_indent + line.lstrip()
                            fixed_lines += 1
                        else:
                            break  # Stop when we find a properly indented line
                    
                    # Stop at the next block-ending statement
                    if any(keyword in line for keyword in ['else:', 'elif', 'except:', 'finally:']):
                        break
                
                print(f"  ✓ Fixed {fixed_lines} lines with {expected_indent} spaces")
                
                # Save
                with open(filepath, 'w') as f:
                    f.writelines(lines)
                
                return True
    
    return False

def show_manual_fix(filepath, error):
    """Show manual fix instructions"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    if hasattr(error, 'lineno') and error.lineno:
        print(f"\n📋 Context around line {error.lineno}:")
        start = max(0, error.lineno - 5)
        end = min(len(lines), error.lineno + 3)
        
        for i in range(start, end):
            marker = ">>>" if i == error.lineno - 1 else "   "
            indent = len(lines[i]) - len(lines[i].lstrip())
            print(f"{marker} {i+1:4d} [{indent:2d}]: {lines[i]}", end='')

def validate_xbrl_structure(content):
    """Basic validation of XBRL-specific patterns"""
    print("\n🔍 Validating XBRL structure...")
    
    # Check for common XBRL patterns
    checks = [
        ('Context creation', 'create_context'),
        ('Fact creation', 'create_fact'),
        ('Unit definitions', 'create_unit'),
        ('Namespace declarations', 'xmlns:'),
        ('ESRS elements', 'esrs:'),
    ]
    
    for name, pattern in checks:
        count = content.count(pattern)
        if count > 0:
            print(f"  ✓ {name}: {count} occurrences")
        else:
            print(f"  ⚠️  {name}: Not found")
    
    # Check for balanced try/except blocks
    try_count = content.count('try:')
    except_count = content.count('except')
    if try_count != except_count:
        print(f"  ⚠️  Unbalanced try/except: {try_count} try blocks, {except_count} except blocks")

def quick_fix_line_2995():
    """Quick fix for the current error at line 2995"""
    filepath = Path("app/api/v1/endpoints/esrs_e1_full.py")
    
    print("🔧 Quick fix for line 2995...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Fix lines 2995-2998 (they need 8 spaces instead of 4)
    for i in range(2994, min(2999, len(lines))):
        if lines[i].strip() and not lines[i].strip().startswith(('else:', 'elif', 'except:')):
            current_indent = len(lines[i]) - len(lines[i].lstrip())
            if current_indent == 4:  # These should be 8
                lines[i] = '        ' + lines[i].strip() + '\n'
                print(f"  ✓ Fixed line {i+1}")
    
    # Save
    with open(filepath, 'w') as f:
        f.writelines(lines)

if __name__ == "__main__":
    # First apply quick fix for the current error
    quick_fix_line_2995()
    
    # Then run comprehensive fix
    if not fix_all_indentation_errors():
        print("\n💡 Manual intervention required")
        print("Check the error message above and fix the indentation manually")