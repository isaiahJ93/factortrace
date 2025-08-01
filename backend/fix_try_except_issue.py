#!/usr/bin/env python3
"""
Fix try/except block issues
"""

import re

def fix_try_except_blocks():
    """Fix issues with try/except blocks"""
    filepath = "app/api/v1/endpoints/esrs_e1_full.py"
    
    print("🔍 INVESTIGATING TRY/EXCEPT ISSUE AT LINE 14476")
    print("=" * 60)
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # First, let's see what's around line 14476
    if len(lines) > 14475:
        print("\n📍 Context around line 14476:")
        for i in range(max(0, 14470), min(len(lines), 14480)):
            marker = ">>>" if i == 14475 else "   "
            print(f"{marker} {i+1}: {lines[i].rstrip()}")
    
    # Look backwards from line 14476 to find the matching try:
    try_line = -1
    indent_level = -1
    
    if len(lines) > 14475:
        # Get the indentation of the except line
        except_line = lines[14475]
        indent_level = len(except_line) - len(except_line.lstrip())
        
        # Search backwards for the matching try:
        for i in range(14474, max(14474 - 1000, 0), -1):
            line = lines[i]
            if line.strip().startswith('try:'):
                line_indent = len(line) - len(line.lstrip())
                if line_indent == indent_level:
                    try_line = i
                    print(f"\n✅ Found matching try: at line {i+1}")
                    break
    
    if try_line == -1:
        print("\n❌ Could not find matching try: statement")
        print("This might be an indentation issue or missing try:")
        return False
    
    # Now check what's between try and except
    print(f"\n🔍 Checking code between try (line {try_line+1}) and except (line 14476)...")
    
    # Look for common issues:
    # 1. Unclosed parentheses/brackets
    # 2. Missing colons
    # 3. Indentation issues
    
    paren_count = 0
    bracket_count = 0
    brace_count = 0
    last_non_empty_line = try_line
    
    for i in range(try_line + 1, 14475):
        line = lines[i]
        if line.strip():  # Non-empty line
            last_non_empty_line = i
            paren_count += line.count('(') - line.count(')')
            bracket_count += line.count('[') - line.count(']')
            brace_count += line.count('{') - line.count('}')
    
    print(f"\n📊 Balance check:")
    print(f"   Parentheses: {paren_count} (should be 0)")
    print(f"   Brackets: {bracket_count} (should be 0)")
    print(f"   Braces: {brace_count} (should be 0)")
    
    fixes_made = False
    
    # If we have unclosed delimiters, try to fix them
    if paren_count > 0:
        print(f"\n🔧 Adding {paren_count} closing parentheses...")
        # Add closing parentheses before the except
        lines[last_non_empty_line] = lines[last_non_empty_line].rstrip() + ')' * paren_count + '\n'
        fixes_made = True
    
    if bracket_count > 0:
        print(f"\n🔧 Adding {bracket_count} closing brackets...")
        lines[last_non_empty_line] = lines[last_non_empty_line].rstrip() + ']' * bracket_count + '\n'
        fixes_made = True
    
    if brace_count > 0:
        print(f"\n🔧 Adding {brace_count} closing braces...")
        lines[last_non_empty_line] = lines[last_non_empty_line].rstrip() + '}' * brace_count + '\n'
        fixes_made = True
    
    if fixes_made:
        # Save the file
        with open(filepath, 'w') as f:
            f.writelines(lines)
        print("\n✅ Applied fixes!")
    else:
        print("\n⚠️ No obvious delimiter issues found")
        print("The issue might be:")
        print("1. Indentation mismatch between try: and except:")
        print("2. Missing colon after a statement")
        print("3. Invalid syntax in the try block")
    
    # Test compilation
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "py_compile", filepath],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("\n🎉 SUCCESS! File compiles without errors!")
        return True
    else:
        print("\n❌ Still has errors:")
        print(result.stderr[:500])
        return False

def main():
    import os
    
    if not os.path.exists("app/api/v1/endpoints/esrs_e1_full.py"):
        print("❌ File not found!")
        return
    
    if fix_try_except_blocks():
        print("\n✅ All syntax errors fixed!")
        print("\n📋 Next steps:")
        print("1. Start server: poetry run uvicorn app.main:app --reload")
        print("2. Test your endpoints")
    else:
        print("\n💡 Manual check needed around line 14476")
        print("Look for:")
        print("- Unclosed parentheses in the try block")
        print("- Indentation mismatches")
        print("- Missing colons")

if __name__ == "__main__":
    main()