#!/usr/bin/env python3
"""
Final fix to remove duplicate if statement and fix indentation
"""

def final_fix():
    filepath = 'app/api/v1/endpoints/esrs_e1_full.py'
    
    print("🔧 Final fix for scoring section...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Show current state
    print("\nCurrent problematic section (lines 3450-3470):")
    for i in range(3449, min(3470, len(lines))):
        print(f"{i+1}: {repr(lines[i])}")
    
    # Identify the issue
    print("\n🔍 Identifying issues:")
    if lines[3452].strip() == 'if weighted_score >= 80:' and lines[3453].strip() == 'if weighted_score >= 80:':
        print("  ❌ Found duplicate 'if' statements at lines 3453 and 3454")
    
    # Fix: Remove duplicate and rebuild the section
    print("\n🔧 Applying fix...")
    
    # Keep everything before line 3453
    new_lines = lines[:3452]
    
    # Add the correct structure
    new_lines.append("    # Determine maturity level\n")
    new_lines.append("    if weighted_score >= 80:\n")
    new_lines.append("        maturity_level = 'Advanced'\n")
    new_lines.append("        description = 'Comprehensive transition plan with strong implementation'\n")
    new_lines.append("    elif weighted_score >= 60:\n")
    new_lines.append("        maturity_level = 'Developing'\n")
    new_lines.append("        description = 'Good foundation with room for enhancement'\n")
    new_lines.append("    elif weighted_score >= 40:\n")
    new_lines.append("        maturity_level = 'Early stage'\n")
    new_lines.append("        description = 'Basic elements in place, significant development needed'\n")
    new_lines.append("    else:\n")
    new_lines.append("        maturity_level = 'Initial'\n")
    new_lines.append("        description = 'Limited transition planning, comprehensive approach needed'\n")
    
    # Find where to continue from (after the problematic section)
    continue_from = None
    for i in range(3465, min(len(lines), 3480)):
        line = lines[i].strip()
        # Find the first line that's not part of the problematic section
        if line and not any(x in line for x in ['description =', 'maturity_level =', 'elif weighted_score', 'else:']):
            if 'Generate recommendations' in line or 'recommendations' in line:
                continue_from = i
                break
    
    if continue_from:
        new_lines.extend(lines[continue_from:])
    else:
        # If we can't find where to continue, just add the rest after our fixed section
        new_lines.extend(lines[3466:])
    
    # Write the fixed file
    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Fixed!")
    
    # Show the fixed section
    print("\nFixed section (lines 3450-3470):")
    for i in range(3449, min(3470, len(new_lines))):
        if i < len(new_lines):
            print(f"{i+1}: {new_lines[i]}", end='')
    
    return True

def verify():
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
        print("\n🎉 Your ESRS E1 iXBRL generator is ready!")
        print("\n🚀 Start your server:")
        print("   uvicorn app.main:app --reload")
        return True
    else:
        print(f"❌ Error: {result.stderr}")
        
        # Show where the error is
        import re
        match = re.search(r'line (\d+)', result.stderr)
        if match:
            error_line = int(match.group(1))
            print(f"\nError at line {error_line}:")
            
            with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
                lines = f.readlines()
            
            if error_line <= len(lines):
                for i in range(max(0, error_line-5), min(len(lines), error_line+3)):
                    marker = ">>>" if i == error_line-1 else "   "
                    print(f"{marker} {i+1}: {lines[i]}", end='')
        
        return False

if __name__ == "__main__":
    # Apply the final fix
    if final_fix():
        # Verify it worked
        verify()