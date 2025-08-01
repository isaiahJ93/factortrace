#!/usr/bin/env python3
"""
Surgical fix for specific syntax errors in ESRS E1 report generator
Targets the exact problematic lines identified in the error trace
"""

def apply_surgical_fix():
    """Apply targeted fixes to specific syntax errors"""
    
    filepath = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    print(f"🔧 Applying surgical fixes to {filepath}")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Fix 1: Line 3279 - Invalid else inside elif block
    # The structure should be:
    # if condition:
    #     ...
    # elif condition:
    #     ...
    # else:
    #     ...
    
    print("\n📍 Fix 1: Restructuring targets_data logic (lines 3275-3282)")
    
    # Find and fix the problematic section
    for i in range(3270, min(3285, len(lines))):
        if i < len(lines):
            line = lines[i]
            line_num = i + 1
            stripped = line.strip()
            
            # Found the problematic else at line 3279
            if line_num == 3279 and stripped == 'else:':
                # This else is inside the elif block - remove it
                # The logic should be: if the data is a list, use it directly
                print(f"  - Removing invalid else at line {line_num}")
                lines[i] = ''  # Remove the line
                if i+1 < len(lines) and 'targets_list' in lines[i+1]:
                    lines[i+1] = ''  # Remove the assignment under it too
    
    # Now add the proper else block at the correct indentation
    # Find where to insert it (after the elif block ends)
    insert_pos = None
    for i in range(3270, min(3285, len(lines))):
        if i < len(lines) and 'elif isinstance(targets_data, list):' in lines[i]:
            # Find the end of this elif block
            elif_indent = len(lines[i]) - len(lines[i].lstrip())
            j = i + 1
            while j < len(lines) and len(lines[j].strip()) > 0:
                current_indent = len(lines[j]) - len(lines[j].lstrip())
                if current_indent <= elif_indent:
                    break
                j += 1
            insert_pos = j
            break
    
    if insert_pos and insert_pos < len(lines):
        # Insert proper else block
        else_block = f"{' ' * 4}else:\n{' ' * 8}targets_list = []\n"
        lines.insert(insert_pos, else_block)
        print(f"  - Added proper else block at line {insert_pos + 1}")
    
    # Fix 2: Line 3456 - elif alignment issue
    print("\n📍 Fix 2: Fixing elif alignment for weighted_score (around line 3456)")
    
    # Search around line 3456 for the scoring logic
    for i in range(max(0, 3450), min(3470, len(lines))):
        if i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Fix elif alignment
            if 'elif weighted_score >=' in stripped:
                # Find the parent if statement
                parent_indent = None
                for j in range(i-1, max(0, i-10), -1):
                    if 'if weighted_score >=' in lines[j]:
                        parent_indent = len(lines[j]) - len(lines[j].lstrip())
                        break
                
                if parent_indent is not None:
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent != parent_indent:
                        lines[i] = ' ' * parent_indent + stripped + '\n'
                        print(f"  - Fixed elif alignment at line {i+1}")
    
    # Fix 3: Check for any other obvious indentation issues
    print("\n📍 Fix 3: General indentation cleanup")
    
    # Common patterns that cause issues
    fixes = 0
    for i in range(len(lines)):
        line = lines[i]
        stripped = line.strip()
        
        # Check for common issues
        if stripped in ['else:', 'elif:', 'except:', 'finally:']:
            # These should never appear alone
            print(f"  - Warning: Incomplete {stripped} at line {i+1}")
            if stripped == 'elif:':
                lines[i] = line.replace('elif:', 'elif True:  # FIX: Add condition\n')
                fixes += 1
    
    print(f"  - Applied {fixes} general fixes")
    
    # Write the fixed file
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    print("\n✅ Surgical fixes applied!")
    
    # Quick validation
    print("\n🔍 Quick syntax check...")
    import subprocess
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', filepath],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Python syntax is valid!")
        return True
    else:
        print("❌ Syntax errors remain:")
        print(result.stderr)
        
        # Try to extract line number
        import re
        match = re.search(r'line (\d+)', result.stderr)
        if match:
            error_line = int(match.group(1))
            print(f"\nError context around line {error_line}:")
            start = max(0, error_line - 5)
            end = min(len(lines), error_line + 3)
            for i in range(start, end):
                marker = ">>>" if i == error_line - 1 else "   "
                print(f"{marker} {i+1:4d}: {lines[i].rstrip()}")
        
        return False

def create_proper_structure_example():
    """Show the correct structure for reference"""
    
    correct_structure = '''
# CORRECT STRUCTURE for targets_data processing:

def process_targets_correctly(data):
    """Example of correct if/elif/else structure"""
    targets_data = data.get('targets', {})
    
    # Proper if/elif/else at same indentation level
    if isinstance(targets_data, dict):
        base_year = targets_data.get('base_year')
        base_emissions = targets_data.get('base_emissions', 0)
        targets_list = targets_data.get('targets', [])
    elif isinstance(targets_data, list):
        base_year = None
        base_emissions = 0
        targets_list = targets_data
    else:  # This else is at the SAME level as if/elif
        targets_list = []
    
    # Continue processing
    if targets_list:
        for target in targets_list:
            process_target(target)

# CORRECT STRUCTURE for scoring:

def calculate_score_correctly(weighted_score):
    """Example of correct scoring structure"""
    if weighted_score >= 80:
        rating = "A"
        color = "green"
    elif weighted_score >= 60:  # Same indent as if
        rating = "B" 
        color = "yellow"
    elif weighted_score >= 40:  # Same indent as if
        rating = "C"
        color = "orange"
    else:  # Same indent as if
        rating = "D"
        color = "red"
    
    return rating, color
'''
    
    print("\n📚 Correct structure example:")
    print(correct_structure)

import sys

if __name__ == "__main__":
    # Show correct structure first
    create_proper_structure_example()
    
    # Apply the fixes
    success = apply_surgical_fix()
    
    if success:
        print("\n🎉 SUCCESS! Your ESRS E1 generator should now run!")
        print("\n🚀 Next steps:")
        print("1. Restart uvicorn: uvicorn app.main:app --reload")
        print("2. Test the /esrs/e1/full endpoint")
        print("3. Validate XBRL output structure")
    else:
        print("\n⚠️  Additional manual fixes needed")
        print("Check the error line and ensure:")
        print("- All if/elif/else are at the same indentation level")
        print("- No else/elif blocks are nested inside other blocks")
        print("- All code blocks have proper indentation")