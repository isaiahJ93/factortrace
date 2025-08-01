#!/usr/bin/env python3
"""
Remove duplicate lines and fix indentation in the scoring section
"""

def fix_duplicates_and_indentation():
    filepath = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    print("🔧 Removing duplicates and fixing indentation...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # First, let's see what we're dealing with around line 3450-3470
    print("\nCurrent state (lines 3450-3470):")
    for i in range(3449, min(3470, len(lines))):
        print(f"{i+1}: {repr(lines[i])}")
    
    # Remove duplicate description lines and fix indentation
    # We'll build a new list of lines
    new_lines = lines[:3453]  # Keep everything up to line 3453
    
    # Manually rebuild the correct structure for lines 3453-3466
    correct_structure = [
        "    if weighted_score >= 80:\n",
        "        maturity_level = 'Advanced'\n",
        "        description = 'Comprehensive transition plan with strong implementation'\n",
        "    elif weighted_score >= 60:\n",
        "        maturity_level = 'Developing'\n", 
        "        description = 'Good foundation with room for enhancement'\n",
        "    elif weighted_score >= 40:\n",
        "        maturity_level = 'Early stage'\n",
        "        description = 'Basic elements in place, significant development needed'\n",
        "    else:\n",
        "        maturity_level = 'Initial'\n",
        "        description = 'Limited transition planning, comprehensive approach needed'\n",
    ]
    
    # Add the correct structure
    new_lines.extend(correct_structure)
    
    # Skip to after the problematic section (find where the duplicates end)
    # Look for the line after all the duplicates
    skip_to = 3466  # Start checking from here
    for i in range(3465, min(len(lines), 3480)):
        line = lines[i].strip()
        # Find the first line that's not a duplicate description
        if line and not line.startswith('description ='):
            skip_to = i
            break
    
    # Add the rest of the file
    new_lines.extend(lines[skip_to:])
    
    # Write the fixed file
    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    
    print(f"\n✅ Removed duplicates and fixed indentation!")
    print(f"Rebuilt lines 3453-3465 with correct structure")
    
    # Show the fixed section
    print("\nFixed section (lines 3450-3470):")
    for i in range(3449, min(3470, len(new_lines))):
        if i < len(new_lines):
            print(f"{i+1}: {new_lines[i]}", end='')

def alternative_fix():
    """Alternative approach using line-by-line processing"""
    filepath = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    print("\n🔧 Alternative fix approach...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Process lines and remove duplicates
    new_lines = []
    skip_next = False
    
    for i, line in enumerate(lines):
        # Skip duplicate description lines
        if skip_next:
            skip_next = False
            continue
            
        # Check if this is a description line
        if 'description =' in line and i < len(lines) - 1:
            # Check if next line is also a description line (duplicate)
            if 'description =' in lines[i + 1]:
                # Keep the one with proper indentation (8 spaces)
                if len(line) - len(line.lstrip()) == 8:
                    new_lines.append(line)
                    skip_next = True
                else:
                    # Skip this one, keep the next
                    continue
            else:
                # Not a duplicate, fix indentation if needed
                if line.strip().startswith('description ='):
                    # Ensure it has 8 spaces
                    new_lines.append('        ' + line.strip() + '\n')
                else:
                    new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Write back
    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Alternative fix applied!")

def verify_fix():
    """Verify the syntax is correct"""
    import subprocess
    import sys
    
    print("\n🔍 Verifying syntax...")
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', 'app/api/v1/endpoints/esrs_e1_full.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ SUCCESS! Python syntax is valid!")
        print("\n🎉 Your ESRS E1 iXBRL generator is ready!")
        print("\n🚀 Next steps:")
        print("1. Restart the server: uvicorn app.main:app --reload")
        print("2. Test the endpoint: /api/v1/esrs/e1/full")
        return True
    else:
        print(f"❌ Error: {result.stderr}")
        return False

if __name__ == "__main__":
    # Try the main fix
    fix_duplicates_and_indentation()
    
    # Verify
    if not verify_fix():
        print("\n🔄 Trying alternative approach...")
        alternative_fix()
        verify_fix()