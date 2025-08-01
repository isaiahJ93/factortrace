#!/usr/bin/env python3
"""
Diagnose and fix the issue around line 951 that's causing a loop.
"""
import subprocess
import re

def diagnose_line_951():
    """Show what's happening around line 951."""
    filename = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    print("🔍 Diagnosing the issue around line 951...")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    print("\nContext around line 951:")
    for i in range(max(0, 945), min(len(lines), 960)):
        marker = ">>>" if i == 950 else "   "
        print(f"{marker} {i+1:4d}: {repr(lines[i])}")
    
    # Check current syntax error
    result = subprocess.run(
        ['python3', '-m', 'py_compile', filename],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"\nCurrent error: {result.stderr}")
    
    # Now let's fix it properly
    print("\n🔧 Applying smart fix...")
    
    # The else: is on line 951, we need to find the first non-empty line after it
    for i in range(951, min(len(lines), 970)):
        line = lines[i].strip()
        if line and not line.startswith('#'):
            # This is the first real code line after else:
            print(f"Found first code line after else: at line {i+1}")
            # Indent it properly (else is at 4 spaces, so content should be at 8)
            lines[i] = '        ' + lines[i].lstrip()
            print(f"Fixed line {i+1}: added proper indentation")
            
            # Also fix any subsequent lines that are part of the else block
            j = i + 1
            while j < len(lines) and j < i + 10:  # Check next 10 lines
                if lines[j].strip() and not lines[j].strip().startswith('#'):
                    current_indent = len(lines[j]) - len(lines[j].lstrip())
                    if current_indent < 8:
                        lines[j] = '        ' + lines[j].lstrip()
                        print(f"Fixed line {j+1}: added proper indentation")
                    elif current_indent == 8:
                        # Already properly indented
                        pass
                    else:
                        # This line starts a new block, stop
                        break
                j += 1
            break
    
    # Write the fix
    with open(filename, 'w') as f:
        f.writelines(lines)
    
    # Test again
    result = subprocess.run(
        ['python3', '-m', 'py_compile', filename],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("\n✅ Fixed successfully!")
        return True
    else:
        print(f"\n❌ Still has error: {result.stderr}")
        return False

def fix_remaining_issues():
    """Fix any remaining indentation issues."""
    filename = 'app/api/v1/endpoints/esrs_e1_full.py'
    max_attempts = 10
    
    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(
            ['python3', '-m', 'py_compile', filename],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n🎉 SUCCESS after fixing {attempt} issues!")
            return True
        
        error = result.stderr
        
        # Handle "expected an indented block"
        if 'expected an indented block after' in error:
            match = re.search(r"after '.*' statement on line (\d+)", error)
            if match:
                control_line = int(match.group(1))
                print(f"\n🔧 Fix #{attempt}: Need to indent after line {control_line}")
                
                with open(filename, 'r') as f:
                    lines = f.readlines()
                
                # Find the first non-empty, non-comment line after the control statement
                found = False
                for i in range(control_line, min(len(lines), control_line + 20)):
                    if lines[i].strip() and not lines[i].strip().startswith('#'):
                        # Get control statement indent
                        control_indent = len(lines[control_line - 1]) - len(lines[control_line - 1].lstrip())
                        expected_indent = control_indent + 4
                        
                        # Indent this line
                        lines[i] = ' ' * expected_indent + lines[i].lstrip()
                        print(f"  ✓ Indented line {i+1} to {expected_indent} spaces")
                        found = True
                        break
                
                if found:
                    with open(filename, 'w') as f:
                        f.writelines(lines)
                else:
                    print("  ⚠️  Couldn't find a line to indent")
                    break
        
        # Handle indentation mismatches
        elif 'unindent does not match' in error:
            match = re.search(r'line (\d+)', error)
            if match:
                error_line = int(match.group(1))
                print(f"\n🔧 Fix #{attempt}: Fixing mismatch at line {error_line}")
                
                with open(filename, 'r') as f:
                    lines = f.readlines()
                
                # Look at the context to determine correct indentation
                idx = error_line - 1
                if idx > 0:
                    # Check previous non-empty line
                    for i in range(idx - 1, max(0, idx - 10), -1):
                        if lines[i].strip():
                            ref_indent = len(lines[i]) - len(lines[i].lstrip())
                            lines[idx] = ' ' * ref_indent + lines[idx].lstrip()
                            print(f"  ✓ Aligned line {error_line} to {ref_indent} spaces")
                            break
                
                with open(filename, 'w') as f:
                    f.writelines(lines)
        else:
            print(f"\n⚠️  Unknown error: {error}")
            break
    
    return False

def main():
    print("=" * 60)
    print("Diagnose and Fix Line 951 Issue")
    print("=" * 60)
    
    # First diagnose and fix the line 951 issue
    if diagnose_line_951():
        print("\n✅ Fixed the line 951 issue!")
        
        # Now fix any remaining issues
        print("\n🔄 Checking for remaining issues...")
        if fix_remaining_issues():
            print("\n🏆 COMPLETE SUCCESS!")
            print("Your ESRS report generator should now start!")
        else:
            print("\n⚠️  Some issues remain")
    else:
        print("\n❌ Could not fix the line 951 issue")
        print("Manual inspection required")
    
    return 0

if __name__ == "__main__":
    exit(main())