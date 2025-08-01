#!/usr/bin/env python3
"""
Fix indentation mismatch issues where lines within the same block have different indentation.
"""
import re
import subprocess

def fix_indentation_mismatches():
    """Fix lines that have inconsistent indentation within the same block."""
    
    filename = 'app/api/v1/endpoints/esrs_e1_full.py'
    print(f"🔧 Fixing indentation mismatches in {filename}...")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    fixed_count = 0
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            i += 1
            continue
        
        current_indent = len(line) - len(line.lstrip())
        
        # Look for the start of a block (lines ending with ':')
        if line.rstrip().endswith(':'):
            block_indent = current_indent + 4
            
            # Find all lines that belong to this block
            j = i + 1
            block_lines = []
            
            while j < len(lines):
                next_line = lines[j]
                
                # Skip empty lines
                if not next_line.strip():
                    j += 1
                    continue
                
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If we've dedented back to or past the original level, block is done
                if next_indent <= current_indent:
                    break
                
                # This line is part of the block
                if next_line.strip():
                    block_lines.append((j, next_indent))
                
                j += 1
            
            # Check if all lines in the block have consistent indentation
            if block_lines:
                # Find the most common indentation in the block
                indents = [indent for _, indent in block_lines]
                most_common_indent = max(set(indents), key=indents.count)
                
                # Fix lines that don't match the most common indentation
                for line_idx, line_indent in block_lines:
                    if line_indent != most_common_indent:
                        # Special case: if the line starts a new block, it might be correct
                        if lines[line_idx].rstrip().endswith(':'):
                            continue
                        
                        lines[line_idx] = ' ' * most_common_indent + lines[line_idx].lstrip()
                        print(f"  Fixed line {line_idx + 1}: adjusted from {line_indent} to {most_common_indent} spaces")
                        fixed_count += 1
        
        i += 1
    
    # Special fix for the specific issue at line 1034
    # Lines 1033-1036 should all have the same indentation
    if len(lines) > 1036:
        # Get the indentation of line 1033 (index 1032)
        ref_indent = len(lines[1032]) - len(lines[1032].lstrip())
        
        # Fix lines 1034-1036 to match
        for idx in [1033, 1034, 1035]:
            if idx < len(lines):
                current = len(lines[idx]) - len(lines[idx].lstrip())
                if current != ref_indent:
                    lines[idx] = ' ' * ref_indent + lines[idx].lstrip()
                    print(f"  Fixed line {idx + 1}: matched indentation with line 1033")
                    fixed_count += 1
    
    # Write the fixed file
    with open(filename, 'w') as f:
        f.writelines(lines)
    
    print(f"\n✅ Fixed {fixed_count} indentation mismatches")
    return fixed_count

def check_and_fix_specific_line(line_no):
    """Fix a specific line based on its context."""
    filename = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    if line_no > len(lines):
        return False
    
    idx = line_no - 1  # Convert to 0-based index
    
    # Find the parent block's indentation
    parent_indent = None
    for i in range(idx - 1, -1, -1):
        if lines[i].rstrip().endswith(':'):
            parent_indent = len(lines[i]) - len(lines[i].lstrip())
            break
    
    if parent_indent is not None:
        expected_indent = parent_indent + 4
        current_indent = len(lines[idx]) - len(lines[idx].lstrip())
        
        if current_indent != expected_indent:
            lines[idx] = ' ' * expected_indent + lines[idx].lstrip()
            print(f"  Fixed line {line_no}: adjusted to {expected_indent} spaces (parent block at {parent_indent})")
            
            with open(filename, 'w') as f:
                f.writelines(lines)
            return True
    
    return False

def main():
    print("=" * 60)
    print("Fix Indentation Mismatch Issues")
    print("=" * 60)
    
    # First, fix general mismatches
    fix_indentation_mismatches()
    
    # Validate
    result = subprocess.run(
        ['python3', '-m', 'py_compile', 'app/api/v1/endpoints/esrs_e1_full.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("\n🎉 SUCCESS! All indentation issues are fixed!")
        return 0
    
    # If still errors, try to fix specific lines
    print(f"\n❌ Still has errors: {result.stderr}")
    
    # Extract line number
    match = re.search(r'line (\d+)', result.stderr)
    if match:
        error_line = int(match.group(1))
        print(f"\n🎯 Attempting to fix line {error_line} specifically...")
        
        if check_and_fix_specific_line(error_line):
            # Validate again
            result = subprocess.run(
                ['python3', '-m', 'py_compile', 'app/api/v1/endpoints/esrs_e1_full.py'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("\n🎉 SUCCESS! All indentation issues are fixed!")
                return 0
            else:
                print(f"\n❌ Still has errors: {result.stderr}")
    
    print("\n💡 Manual inspection may be needed for complex nested structures.")
    return 1

if __name__ == "__main__":
    exit(main())