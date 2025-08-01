#!/usr/bin/env python3
"""
Fix ALL the syntax errors Claude Opus 4 identified
"""

import re
import shutil
from datetime import datetime

def fix_all_syntax_errors():
    """Fix all identified syntax errors in one pass"""
    filepath = "app/api/v1/endpoints/esrs_e1_full.py"
    
    print("🔧 FIXING ALL SYNTAX ERRORS CLAUDE FOUND")
    print("=" * 60)
    
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_claude_fixes_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    fixes_applied = []
    
    # Fix 1: Lines with missing ): after get()
    missing_paren_lines = [1270, 1280, 1290, 1389, 1743]
    for line_num in missing_paren_lines:
        if line_num - 1 < len(lines):
            if "get(" in lines[line_num - 1] and lines[line_num - 1].rstrip().endswith("{}"):
                lines[line_num - 1] = lines[line_num - 1].rstrip() + "):\n"
                fixes_applied.append(f"Line {line_num}: Added ): after get()")
    
    # Fix 2: Line 2994 - +) should be +
    if len(lines) > 2993:
        lines[2993] = lines[2993].replace("+)", "+")
        fixes_applied.append("Line 2994: Changed +) to +")
    
    # Fix 3: Line 3501 - certificate_details = []):
    if len(lines) > 3500:
        lines[3500] = lines[3500].replace("]):", "]")
        fixes_applied.append("Line 3501: Removed ): after []")
    
    # Fix 4: Line 2761 - Dictionary ending with ,):
    if len(lines) > 2760:
        lines[2760] = lines[2760].replace(",):", ",")
        fixes_applied.append("Line 2761: Changed ,): to ,")
    
    # Fix 5: Line 2851 - 'by_sector': {}):
    if len(lines) > 2850:
        lines[2850] = lines[2850].replace("{}):", "{}}")
        fixes_applied.append("Line 2851: Changed {}): to {}}")
    
    # Fix 6: Line 2997 - 'methodology': 'IPCC AR6 risk framework'):
    if len(lines) > 2996:
        lines[2996] = lines[2996].replace("'):", "'}")
        fixes_applied.append("Line 2997: Changed '): to '}")
    
    # Fix 7: Line 1593 - f-string with mismatched parentheses
    if len(lines) > 1592:
        # Fix the f-string to have balanced parentheses
        line = lines[1592]
        if "({cat_enum.value[0]})" in line:
            # Move the ) outside the f-string expression
            lines[1592] = line.replace("({cat_enum.value[0]})", "({cat_enum.value[0]})")
            if lines[1592].endswith("))\n"):
                lines[1592] = lines[1592][:-2] + "\n"
            fixes_applied.append("Line 1593: Fixed f-string parentheses")
    
    # Fix 8: Function definitions missing ):
    # Line 2927-2944 and others
    function_lines = [2932, 2874]  # Lines after which we need to add ):
    for line_num in function_lines:
        if line_num < len(lines):
            # Check if the next line is a docstring
            if line_num + 1 < len(lines) and (lines[line_num + 1].strip().startswith('"""') or 
                                              lines[line_num + 1].strip().startswith("'''")):
                # Insert ): before the docstring
                lines.insert(line_num + 1, "):\n")
                fixes_applied.append(f"Line {line_num + 1}: Added ): for function definition")
    
    # Fix 9: Remove stray } characters
    stray_brace_lines = [2944, 3831]
    for line_num in sorted(stray_brace_lines, reverse=True):  # Process in reverse to maintain line numbers
        if line_num - 1 < len(lines) and lines[line_num - 1].strip() == "}":
            del lines[line_num - 1]
            fixes_applied.append(f"Line {line_num}: Removed stray }}")
    
    # Fix 10: Missing closing parentheses in calculations
    # Line 883 - energy calculation
    if len(lines) > 887:
        # Check if line 887 ends the calculation without )
        if "fuel_combustion_mwh" in lines[886] and not lines[887].strip().startswith(")"):
            lines.insert(887, "        )\n")
            fixes_applied.append("Line 888: Added closing ) for energy calculation")
    
    # Save the fixed file
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    print(f"\n✅ Applied {len(fixes_applied)} fixes:")
    for fix in fixes_applied:
        print(f"   - {fix}")
    
    # Test compilation
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "py_compile", filepath],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("\n🎉 SUCCESS! File compiles without errors!")
        return True
    else:
        print("\n❌ Still has errors:")
        print(result.stderr)
        return False

def main():
    import os
    
    if not os.path.exists("app/api/v1/endpoints/esrs_e1_full.py"):
        print("❌ File not found!")
        return
    
    if fix_all_syntax_errors():
        print("\n" + "=" * 60)
        print("✅ ALL SYNTAX ERRORS FIXED!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("1. Test import: python3 -c \"from app.api.v1.endpoints.esrs_e1_full import create_proper_ixbrl_report\"")
        print("2. Start server: poetry run uvicorn app.main:app --reload")
        print("\n🚀 Your iXBRL generator is ready!")
    else:
        print("\n⚠️ Some errors remain. Check the output above.")

if __name__ == "__main__":
    main()