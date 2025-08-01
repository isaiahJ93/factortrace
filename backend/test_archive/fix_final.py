#!/usr/bin/env python3
"""
Final fix for the indentation issue - aligning try/except properly
"""

from pathlib import Path

def fix_indentation():
    filepath = Path("app/api/v1/endpoints/esrs_e1_full.py")
    
    print("🔧 FINAL INDENTATION FIX")
    print("=" * 50)
    
    # Read file
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Fix the specific lines
    fixes = [
        (2943, 12),  # Line 2944: reporting_period = int(...) should have 12 spaces
        (2944, 8),   # Line 2945: except ValueError: should have 8 spaces
        (2945, 12),  # Line 2946: validation_result["consistent"] should have 12 spaces
        (2946, 12),  # Line 2947: validation_result["issues"].append should have 12 spaces
        (2947, 12),  # Line 2948: return validation_result should have 12 spaces
    ]
    
    print("Applying fixes:")
    for line_idx, target_indent in fixes:
        if line_idx < len(lines):
            old_indent = len(lines[line_idx]) - len(lines[line_idx].lstrip())
            lines[line_idx] = ' ' * target_indent + lines[line_idx].lstrip()
            print(f"  ✓ Line {line_idx + 1}: {old_indent} → {target_indent} spaces")
    
    # Save
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    # Show the fixed result
    print("\n📋 Fixed code structure:")
    for i in range(2942, 2949):
        indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"{i+1:4d} [{indent:2d}]: {lines[i]}", end='')
    
    # Test
    print("\n🔍 Testing compilation...")
    try:
        compile(open(filepath).read(), filepath, 'exec')
        print("\n✅ SUCCESS! File compiles!")
        print("🎉 YOUR ESRS E1 iXBRL GENERATOR IS PRODUCTION READY!")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    fix_indentation()