#!/usr/bin/env python3
"""
Fix elif/else statement alignment issues.
"""
import subprocess
import re

def fix_elif_alignment():
    """Fix elif statements that don't align with their corresponding if statements."""
    filename = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    print("🔧 Fixing elif/else alignment issues...")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Show the problem area
    print("\nProblem area (lines 959-970):")
    for i in range(958, min(len(lines), 970)):
        indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"  {i+1:4d} [{indent:2d}]: {repr(lines[i])}")
    
    # Fix elif statements that are misaligned
    fixes_made = 0
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this is an elif or else statement
        if line.startswith('elif ') or (line == 'else:' and i > 0):
            current_indent = len(lines[i]) - len(lines[i].lstrip())
            
            # Look backwards for the matching if statement
            matching_if_indent = None
            for j in range(i - 1, max(0, i - 50), -1):
                if lines[j].lstrip().startswith('if '):
                    # Found a potential matching if
                    if_indent = len(lines[j]) - len(lines[j].lstrip())
                    # Make sure there's no else/elif between this if and our current line at the same level
                    valid_match = True
                    for k in range(j + 1, i):
                        check_line = lines[k].strip()
                        if check_line.startswith(('elif ', 'else:')) and len(lines[k]) - len(lines[k].lstrip()) == if_indent:
                            valid_match = False
                            break
                    if valid_match:
                        matching_if_indent = if_indent
                        break
            
            if matching_if_indent is not None and current_indent != matching_if_indent:
                lines[i] = ' ' * matching_if_indent + lines[i].lstrip()
                print(f"\n✓ Fixed line {i+1}: aligned {line[:20]}... to {matching_if_indent} spaces")
                fixes_made += 1
        
        i += 1
    
    if fixes_made > 0:
        # Write the fixes
        with open(filename, 'w') as f:
            f.writelines(lines)
        
        print(f"\n✅ Made {fixes_made} alignment fixes")
    else:
        print("\n⚠️  No elif/else alignment issues found")
    
    # Test the result
    result = subprocess.run(
        ['python3', '-m', 'py_compile', filename],
        capture_output=True,
        text=True
    )
    
    return result.returncode == 0, result.stderr

def fix_remaining_syntax_issues():
    """Fix any remaining syntax and indentation issues."""
    filename = 'app/api/v1/endpoints/esrs_e1_full.py'
    max_attempts = 10
    
    for attempt in range(1, max_attempts + 1):
        # Check current status
        result = subprocess.run(
            ['python3', '-m', 'py_compile', filename],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n🎉 SUCCESS! All issues fixed!")
            return True
        
        error = result.stderr
        print(f"\n🔧 Attempt {attempt}: {error.split(':', 2)[-1].strip()[:100]}...")
        
        # Handle SyntaxError with elif
        if 'SyntaxError' in error and 'elif' in error:
            match = re.search(r'line (\d+)', error)
            if match:
                line_no = int(match.group(1))
                with open(filename, 'r') as f:
                    lines = f.readlines()
                
                if line_no <= len(lines):
                    # This elif needs to be aligned with its if
                    # The if should be at 8 spaces (inside the else block)
                    lines[line_no - 1] = '        ' + lines[line_no - 1].lstrip()
                    print(f"  ✓ Fixed elif alignment on line {line_no}")
                    
                    with open(filename, 'w') as f:
                        f.writelines(lines)
                    continue
        
        # Handle expected indented block
        elif 'expected an indented block after' in error:
            match = re.search(r"after '(.*)' statement on line (\d+)", error)
            if match:
                control_line = int(match.group(2))
                
                with open(filename, 'r') as f:
                    lines = f.readlines()
                
                # Indent the next code line
                for i in range(control_line, min(len(lines), control_line + 10)):
                    if lines[i].strip() and not lines[i].strip().startswith('#'):
                        control_indent = len(lines[control_line - 1]) - len(lines[control_line - 1].lstrip())
                        lines[i] = ' ' * (control_indent + 4) + lines[i].lstrip()
                        print(f"  ✓ Indented line {i+1}")
                        
                        with open(filename, 'w') as f:
                            f.writelines(lines)
                        break
                continue
        
        # If we can't handle this error
        print(f"  ⚠️  Cannot automatically fix this error")
        return False
    
    return False

def main():
    print("=" * 60)
    print("Fix elif Statement Alignment")
    print("=" * 60)
    
    # First fix elif alignment
    success, error = fix_elif_alignment()
    
    if not success:
        print(f"\n❌ Still has errors after alignment fix: {error}")
        print("\n🔄 Attempting to fix remaining issues...")
        success = fix_remaining_syntax_issues()
    
    if success:
        print("\n🏆 COMPLETE SUCCESS!")
        print("✅ All syntax and indentation issues are fixed!")
        print("🚀 Your ESRS report generator should now be running!")
    else:
        print("\n⚠️  Manual intervention may be needed")
        print("Check the file around the last reported error")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())