#!/usr/bin/env python3
"""
Find ALL unclosed parentheses in the file
"""

def find_unclosed_parens(filepath):
    """Find all lines with unclosed parentheses"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    print("🔍 Finding ALL unclosed parentheses...")
    print("=" * 60)
    
    # Track parentheses balance
    paren_stack = []  # Stack of (line_num, char, position)
    issues = []
    
    for i, line in enumerate(lines):
        for j, char in enumerate(line):
            if char in '([{':
                paren_stack.append((i+1, char, j))
            elif char in ')]}':
                if not paren_stack:
                    issues.append(f"Line {i+1}: Unmatched closing '{char}'")
                else:
                    open_line, open_char, _ = paren_stack.pop()
                    # Check if they match
                    expected = {'(': ')', '[': ']', '{': '}'}
                    if expected.get(open_char) != char:
                        issues.append(f"Line {i+1}: '{char}' doesn't match '{open_char}' from line {open_line}")
                        # Put it back for further checking
                        paren_stack.append((open_line, open_char, _))
    
    # Check for unclosed
    for line_num, char, _ in paren_stack:
        issues.append(f"Line {line_num}: Unclosed '{char}'")
    
    # Find specific patterns that need fixing
    print("\n📍 Lines that likely need ):")
    for i, line in enumerate(lines):
        # Pattern: if x in y.get('key', {}
        if "get(" in line and line.rstrip().endswith("{}"):
            print(f"  Line {i+1}: {line.strip()}")
            print(f"    Fix: Add ): at end")
    
    print("\n📍 All issues found:")
    for issue in issues[:20]:  # Show first 20
        print(f"  {issue}")
    
    if len(issues) > 20:
        print(f"  ... and {len(issues) - 20} more")
    
    # Now let's fix the most common pattern
    print("\n🔧 Fixing common patterns...")
    fixed = 0
    
    for i, line in enumerate(lines):
        # Fix: if x in y.get('key', {} -> if x in y.get('key', {}):
        if "if " in line and "get(" in line and line.rstrip().endswith("{}"):
            lines[i] = line.rstrip() + "):\n"
            fixed += 1
            print(f"  Fixed line {i+1}")
    
    if fixed > 0:
        # Save the fixes
        with open(filepath, 'w') as f:
            f.writelines(lines)
        print(f"\n✅ Fixed {fixed} lines")
    
    return fixed > 0

if __name__ == "__main__":
    import sys
    filepath = "app/api/v1/endpoints/esrs_e1_full.py"
    
    if find_unclosed_parens(filepath):
        print("\n🔍 Testing compilation...")
        import subprocess
        result = subprocess.run(
            ["python3", "-m", "py_compile", filepath],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ File compiles successfully!")
        else:
            print("❌ Still has errors:")
            print(result.stderr[:500])