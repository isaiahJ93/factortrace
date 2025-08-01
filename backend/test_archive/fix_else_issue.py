#!/usr/bin/env python3
"""
Fix the specific else statement issue at line 951
"""

# First, let's examine the problem area
print("🔍 Examining lines around 951...")
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Show context
print("\nContext around line 951:")
for i in range(max(0, 950-5), min(len(lines), 955)):
    print(f"{i+1:4d}: {repr(lines[i])}")

# Fix the specific issue - line 953 needs to be indented
print("\n🔧 Fixing indentation after else statement...")
if len(lines) > 952:  # Check line 953 exists
    # Line 953 should be indented by 4 more spaces than the else:
    current_line = lines[952]  # Line 953 (0-indexed)
    if current_line.strip():  # If not empty
        # The else: is at 4 spaces, so content should be at 8 spaces
        lines[952] = '        ' + current_line.lstrip()
        print(f"Fixed line 953: added proper indentation")

# Also check subsequent lines that might need fixing
for i in range(953, min(len(lines), 970)):
    if lines[i].strip() and not lines[i].startswith('    '):
        # This line probably needs indentation too
        indent_level = 8  # Default indent under else
        # Check if it's a continuation of the else block
        if lines[i].lstrip().startswith(('if ', 'elif ', 'else:', 'for ', 'while ', 'def ', 'class ')):
            indent_level = 4  # Back to main level
        
        if len(lines[i]) - len(lines[i].lstrip()) < indent_level:
            lines[i] = ' ' * indent_level + lines[i].lstrip()
            print(f"Fixed line {i+1}: adjusted indentation")

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("\n✅ Fixed else statement indentation issue")

# Test the fix
import subprocess
result = subprocess.run(['python3', '-m', 'py_compile', 'app/api/v1/endpoints/esrs_e1_full.py'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print("🎉 SUCCESS! The file now compiles correctly!")
else:
    print(f"❌ Still has errors: {result.stderr}")
    # Try to parse the next error
    import re
    match = re.search(r'line (\d+)', result.stderr)
    if match:
        next_line = int(match.group(1))
        print(f"\n📍 Next error is at line {next_line}")
        if next_line < len(lines):
            print(f"   Content: {repr(lines[next_line-1])}")