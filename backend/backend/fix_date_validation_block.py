#!/usr/bin/env python3
"""
Fix the entire date validation block with proper try/except structure
"""

from pathlib import Path

def fix_date_validation_block():
    filepath = Path("app/api/v1/endpoints/esrs_e1_full.py")
    
    print("🔧 FIXING DATE VALIDATION BLOCK")
    print("=" * 50)
    
    # Read the file
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Show current state
    print("\n📋 Current state (lines 2960-2975):")
    for i in range(2959, min(2975, len(lines))):
        indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"{i+1:4d} [{indent:2d}]: {lines[i]}", end='')
    
    # Fix the block systematically
    print("\n🔧 Applying fixes...")
    
    # The structure should be:
    # for section, field in date_fields:  (4 spaces)
    #     if section in data and field in data[section]:  (8 spaces)
    #         value = data[section][field]  (12 spaces)
    #         if isinstance(value, (int, str)):  (12 spaces)
    #             try:  (16 spaces)
    #                 year = int(str(value)[:4])  (20 spaces)
    #                 validation_result["periods_found"].add(year)  (20 spaces)
    #                 if abs(year - reporting_period) > 1 and field != 'base_year':  (20 spaces)
    #                     validation_result["consistent"] = False  (24 spaces)
    #                     validation_result["issues"].append(...)  (24 spaces)
    #             except (ValueError, TypeError):  (16 spaces)
    #                 pass  (20 spaces)
    
    # Fix line by line
    fixes = [
        (2961, 12, "value = data[section][field]"),
        (2962, 12, "if isinstance(value, (int, str)):"),
        (2963, 16, "try:"),
        (2964, 20, "year = int(str(value)[:4])"),
        (2965, 20, "validation_result[\"periods_found\"].add(year)"),
        (2966, 20, "if abs(year - reporting_period) > 1 and field != 'base_year':"),
        (2967, 24, "validation_result[\"consistent\"] = False"),
        (2968, 24, "validation_result[\"issues\"].append("),
        (2969, 28, "f\"{section}.{field} ({year}) not consistent with reporting period ({reporting_period})\""),
    ]
    
    # Apply fixes
    for line_idx, spaces, expected_content in fixes:
        if line_idx < len(lines):
            lines[line_idx] = ' ' * spaces + lines[line_idx].lstrip()
            print(f"  ✓ Fixed line {line_idx + 1} to {spaces} spaces")
    
    # Add the missing except block after the try block content
    # Find where to insert the except
    insert_position = 2970  # After the append statement
    
    # Check if there's already an except block
    has_except = False
    for i in range(2970, min(2975, len(lines))):
        if 'except' in lines[i]:
            has_except = True
            break
    
    if not has_except:
        print("\n  ✓ Adding missing except block")
        # Insert except block
        lines.insert(insert_position, '                    )\n')  # Close the append
        lines.insert(insert_position + 1, '            except (ValueError, TypeError):\n')
        lines.insert(insert_position + 2, '                pass\n')
    
    # Save the fixed file
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    # Show fixed state
    print("\n📋 Fixed state:")
    # Re-read to show current state
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for i in range(2959, min(2975, len(lines))):
        indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"{i+1:4d} [{indent:2d}]: {lines[i]}", end='')
    
    # Test compilation
    print("\n🔍 Testing compilation...")
    try:
        compile(open(filepath).read(), filepath, 'exec')
        print("\n✅ File compiles successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'lineno'):
            print(f"Error at line {e.lineno}")
            # Show context
            start = max(0, e.lineno - 5)
            end = min(len(lines), e.lineno + 3)
            print("\n📋 Context around error:")
            for i in range(start, end):
                marker = ">>>" if i == e.lineno - 1 else "   "
                indent = len(lines[i]) - len(lines[i].lstrip())
                print(f"{marker} {i+1:4d} [{indent:2d}]: {lines[i]}", end='')
        return False

if __name__ == "__main__":
    if not fix_date_validation_block():
        print("\n💡 Manual intervention needed")
        print("The date validation block needs proper try/except structure")
