#!/usr/bin/env python3
"""Fix syntax error in api.py"""

def fix_api_syntax():
    with open("app/api/v1/api.py", "r") as f:
        lines = f.readlines()
    
    # Look for the problematic area around line 371
    for i in range(len(lines)):
        if i > 0 and '"features": {' in lines[i]:
            # Check if previous line needs a comma
            prev_line = lines[i-1].rstrip()
            if prev_line and not prev_line.endswith((',', '{', '[')):
                lines[i-1] = prev_line + ',\n'
                print(f"✅ Added missing comma at line {i}")
    
    # Write back
    with open("app/api/v1/api.py", "w") as f:
        f.writelines(lines)
    
    print("✅ Fixed syntax in app/api/v1/api.py")

if __name__ == "__main__":
    fix_api_syntax()
