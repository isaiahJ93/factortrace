#!/usr/bin/env python3
"""
Fix all if/else/elif indentation issues in one go.
This targets the specific pattern where control flow statements have unindented bodies.
"""
import re
import subprocess

def fix_all_control_blocks():
    """Fix all if/else/elif blocks that are missing indentation."""
    
    filename = 'app/api/v1/endpoints/esrs_e1_full.py'
    print(f"🔧 Fixing ALL control flow blocks in {filename}...")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Pattern: lines ending with ':' that should have indented content after them
    control_patterns = [
        r'^\s*if\s+.*:$',
        r'^\s*elif\s+.*:$',
        r'^\s*else\s*:$',
        r'^\s*for\s+.*:$',
        r'^\s*while\s+.*:$',
        r'^\s*def\s+.*:$',
        r'^\s*class\s+.*:$',
        r'^\s*try\s*:$',
        r'^\s*except.*:$',
        r'^\s*finally\s*:$',
        r'^\s*with\s+.*:$',
    ]
    
    fixed_count = 0
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line is a control statement
        is_control = any(re.match(pattern, line.rstrip()) for pattern in control_patterns)
        
        if is_control:
            current_indent = len(line) - len(line.lstrip())
            expected_body_indent = current_indent + 4
            
            # Find the next non-empty, non-comment line
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                stripped = next_line.strip()
                
                # Skip empty lines and comments
                if not stripped or stripped.startswith('#'):
                    j += 1
                    continue
                
                # This is the first real line after the control statement
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If it's not properly indented, fix it
                if next_indent <= current_indent:
                    lines[j] = ' ' * expected_body_indent + next_line.lstrip()
                    print(f"  Fixed line {j+1}: indented under '{line.strip()}'")
                    fixed_count += 1
                    
                    # Also fix subsequent lines in the same block
                    k = j + 1
                    while k < len(lines):
                        block_line = lines[k]
                        if not block_line.strip():
                            k += 1
                            continue
                        
                        block_indent = len(block_line) - len(block_line.lstrip())
                        
                        # If this line starts a new control structure, stop
                        if any(re.match(pattern, block_line.rstrip()) for pattern in control_patterns):
                            if block_indent <= current_indent:
                                break
                        
                        # If this line is at the wrong indentation level
                        if block_line.strip() and block_indent < expected_body_indent:
                            # Check if it should be at the parent level
                            if block_indent <= current_indent:
                                # This marks the end of the block
                                break
                            else:
                                # This should be part of the block
                                lines[k] = ' ' * expected_body_indent + block_line.lstrip()
                                print(f"  Fixed line {k+1}: continued block indentation")
                                fixed_count += 1
                        
                        k += 1
                
                break  # We found and fixed the first line after control statement
                
            if j >= len(lines):
                # Control statement at end of file with no body
                print(f"  Warning: Control statement at line {i+1} has no body")
        
        i += 1
    
    # Write the fixed file
    with open(filename, 'w') as f:
        f.writelines(lines)
    
    print(f"\n✅ Fixed {fixed_count} indentation issues")
    return fixed_count

def validate_file():
    """Validate the Python syntax."""
    result = subprocess.run(
        ['python3', '-m', 'py_compile', 'app/api/v1/endpoints/esrs_e1_full.py'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0, result.stderr

def main():
    print("=" * 60)
    print("Comprehensive Control Flow Indentation Fix")
    print("=" * 60)
    
    # Keep fixing until no more issues
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n🔄 Iteration {iteration}...")
        
        # Fix control blocks
        fixed = fix_all_control_blocks()
        
        # Validate
        valid, error = validate_file()
        
        if valid:
            print("\n🎉 SUCCESS! All indentation issues are fixed!")
            print("Your ESRS report generator should now start successfully.")
            return 0
        
        if fixed == 0:
            # No fixes were made, but there's still an error
            print(f"\n❌ Still has errors but no obvious indentation issues found:")
            print(error)
            
            # Try to extract line number for manual inspection
            match = re.search(r'line (\d+)', error)
            if match:
                line_no = int(match.group(1))
                print(f"\n📍 Check line {line_no} manually")
                
                # Show context
                with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
                    lines = f.readlines()
                
                if line_no <= len(lines):
                    start = max(0, line_no - 5)
                    end = min(len(lines), line_no + 5)
                    print("\nContext:")
                    for i in range(start, end):
                        marker = ">>>" if i == line_no - 1 else "   "
                        print(f"{marker} {i+1:4d}: {repr(lines[i])}")
            
            return 1
        
        print(f"  Continuing to next iteration...")
    
    print(f"\n⚠️  Reached maximum iterations ({max_iterations})")
    return 1

if __name__ == "__main__":
    exit(main())