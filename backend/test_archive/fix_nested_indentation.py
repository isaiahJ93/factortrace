#!/usr/bin/env python3
"""
Fix nested indentation issues - handle if statements inside else blocks.
"""
import subprocess
import re

def fix_nested_indentation():
    """Fix all nested indentation issues systematically."""
    filename = 'app/api/v1/endpoints/esrs_e1_full.py'
    max_attempts = 20
    attempt = 0
    
    print("🔧 Fixing nested indentation issues...")
    
    while attempt < max_attempts:
        attempt += 1
        
        # Try to compile
        result = subprocess.run(
            ['python3', '-m', 'py_compile', filename],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS after {attempt} fixes!")
            return True
        
        error = result.stderr
        
        # Handle "expected an indented block"
        if 'expected an indented block after' in error:
            match = re.search(r"after '(.*)' statement on line (\d+)", error)
            if match:
                statement_type = match.group(1)
                control_line = int(match.group(2))
                
                print(f"\n🔧 Fix #{attempt}: Need indentation after '{statement_type}' on line {control_line}")
                
                with open(filename, 'r') as f:
                    lines = f.readlines()
                
                if control_line <= len(lines):
                    # Get the indentation of the control statement
                    control_indent = len(lines[control_line - 1]) - len(lines[control_line - 1].lstrip())
                    expected_indent = control_indent + 4
                    
                    # Find the next non-empty, non-comment line
                    fixed = False
                    for i in range(control_line, min(len(lines), control_line + 10)):
                        line = lines[i].strip()
                        if line and not line.startswith('#'):
                            # This needs indentation
                            current_indent = len(lines[i]) - len(lines[i].lstrip())
                            if current_indent < expected_indent:
                                lines[i] = ' ' * expected_indent + lines[i].lstrip()
                                print(f"  ✓ Indented line {i+1} from {current_indent} to {expected_indent} spaces")
                                fixed = True
                                
                                # If this was an if/elif/else, we might need to fix multiple lines
                                if statement_type in ['if', 'elif', 'else']:
                                    # Check next few lines that might be part of the block
                                    for j in range(i + 1, min(len(lines), i + 20)):
                                        if lines[j].strip() and not lines[j].strip().startswith('#'):
                                            j_indent = len(lines[j]) - len(lines[j].lstrip())
                                            # If it's less indented than expected and not a new control statement
                                            if j_indent < expected_indent and not any(lines[j].lstrip().startswith(x) for x in ['if ', 'elif ', 'else:', 'for ', 'while ', 'def ', 'class ', 'try:', 'except']):
                                                lines[j] = ' ' * expected_indent + lines[j].lstrip()
                                                print(f"  ✓ Also indented line {j+1} to {expected_indent} spaces")
                                            elif j_indent >= expected_indent:
                                                # Properly indented or start of new block
                                                break
                                break
                    
                    if fixed:
                        with open(filename, 'w') as f:
                            f.writelines(lines)
                    else:
                        print("  ⚠️  Couldn't find line to indent")
                        break
        
        # Handle indentation mismatches
        elif 'unindent does not match' in error:
            match = re.search(r'line (\d+)', error)
            if match:
                error_line = int(match.group(1))
                print(f"\n🔧 Fix #{attempt}: Fixing mismatch at line {error_line}")
                
                with open(filename, 'r') as f:
                    lines = f.readlines()
                
                if error_line <= len(lines):
                    # Find the proper indentation level
                    idx = error_line - 1
                    
                    # Look backwards for context
                    proper_indent = 0
                    for i in range(idx - 1, max(0, idx - 20), -1):
                        if lines[i].strip():
                            if lines[i].rstrip().endswith(':'):
                                # This is a control statement, our line should be indented under it
                                proper_indent = len(lines[i]) - len(lines[i].lstrip()) + 4
                                break
                            elif not lines[i].lstrip().startswith('#'):
                                # Regular code line at same level
                                proper_indent = len(lines[i]) - len(lines[i].lstrip())
                                break
                    
                    lines[idx] = ' ' * proper_indent + lines[idx].lstrip()
                    print(f"  ✓ Fixed line {error_line} to {proper_indent} spaces")
                    
                    with open(filename, 'w') as f:
                        f.writelines(lines)
        
        else:
            print(f"\n⚠️  Unknown error: {error}")
            break
    
    print(f"\n❌ Reached maximum attempts ({max_attempts})")
    return False

def show_current_state():
    """Show the current state around problem areas."""
    filename = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    print("\n📋 Current state check:")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Show area around line 955
    print("\nArea around line 955:")
    for i in range(max(0, 950), min(len(lines), 965)):
        indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"  {i+1:4d} [{indent:2d}]: {repr(lines[i])}")

def main():
    print("=" * 60)
    print("Fix Nested Indentation Issues")
    print("=" * 60)
    
    # Show current state
    show_current_state()
    
    # Fix issues
    if fix_nested_indentation():
        print("\n🎉 ALL INDENTATION ISSUES FIXED!")
        print("Your ESRS report generator should now be running!")
        print("\n✅ Summary of fixes:")
        print("  - Fixed else block indentation")
        print("  - Fixed nested if statements")
        print("  - Resolved all control flow indentation")
        print("\n🚀 Check your server - it should be running now!")
    else:
        print("\n⚠️  Some issues remain")
        print("Check the last error message for details")
    
    return 0

if __name__ == "__main__":
    exit(main())