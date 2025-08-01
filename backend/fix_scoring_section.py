#!/usr/bin/env python3
"""
Fix the scoring section indentation issues
"""

def fix_scoring_section():
    filepath = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    print("🔧 Fixing scoring section indentation...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # The problematic section is around lines 3453-3465
    # We need to fix the if/elif/else structure
    
    fixes = [
        # (line_number, correct_content)
        (3456, "        description = 'Comprehensive transition plan with strong implementation'\n"),
        (3457, "    elif weighted_score >= 60:\n"),
        (3459, "        description = 'Good foundation with room for enhancement'\n"),
        (3460, "    elif weighted_score >= 40:\n"),
        (3462, "        description = 'Basic elements in place, significant development needed'\n"),
        (3463, "    else:\n"),
        (3465, "        description = 'Limited transition planning, comprehensive approach needed'\n"),
    ]
    
    for line_num, correct_content in fixes:
        if line_num <= len(lines):
            old_content = lines[line_num - 1]
            lines[line_num - 1] = correct_content
            print(f"  Line {line_num}: Fixed indentation")
    
    # Write the fixed file
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    print("\n✅ Fixed scoring section!")
    
    # Show the fixed section
    print("\nFixed section (lines 3450-3467):")
    for i in range(3449, min(3467, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')
    
    return True

def verify_fix():
    """Verify the fix worked"""
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
        print("\n🚀 Your ESRS E1 generator is ready to run!")
        print("Start the server: uvicorn app.main:app --reload")
        return True
    else:
        print(f"❌ Error: {result.stderr}")
        # Extract line number
        import re
        match = re.search(r'line (\d+)', result.stderr)
        if match:
            error_line = int(match.group(1))
            print(f"\nError remains at line {error_line}")
            
            # Show context
            with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
                lines = f.readlines()
            
            if error_line <= len(lines):
                print("\nContext:")
                for i in range(max(0, error_line-5), min(len(lines), error_line+3)):
                    marker = ">>>" if i == error_line-1 else "   "
                    print(f"{marker} {i+1}: {lines[i]}", end='')
        return False

if __name__ == "__main__":
    # Apply the fix
    if fix_scoring_section():
        # Verify it worked
        if verify_fix():
            print("\n✨ All done! Your ESRS E1 iXBRL generator is ready!")
        else:
            print("\n⚠️  There might be more similar issues in the file.")
            print("Run this script again or check other if/elif/else blocks.")