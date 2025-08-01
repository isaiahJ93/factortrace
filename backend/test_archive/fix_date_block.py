#!/usr/bin/env python3
from pathlib import Path

filepath = Path("app/api/v1/endpoints/esrs_e1_full.py")

# Read the file
with open(filepath, 'r') as f:
    lines = f.readlines()

print("Fixing date validation block indentation...")
print("\nBefore:")
for i in range(2959, 2970):
    if i < len(lines):
        indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"{i+1:4d} [{indent:2d}]: {lines[i]}", end='')

# Fix the indentation
# Line 2962 should be indented inside the if (12 spaces)
if len(lines) > 2961:
    lines[2961] = '            ' + lines[2961].lstrip()  # 12 spaces
    
# Line 2963 should also be at 12 spaces
if len(lines) > 2962:
    lines[2962] = '            ' + lines[2962].lstrip()  # 12 spaces
    
# Line 2964 (try:) should be at 16 spaces
if len(lines) > 2963:
    lines[2963] = '                ' + lines[2963].lstrip()  # 16 spaces
    
# Line 2965 should be inside try (20 spaces)
if len(lines) > 2964:
    lines[2964] = '                    ' + lines[2964].lstrip()  # 20 spaces

# Continue fixing following lines if needed
for i in range(2965, min(2975, len(lines))):
    line = lines[i]
    if 'except' in line and 'ValueError' in line:
        # except should align with try (16 spaces)
        lines[i] = '                ' + line.lstrip()
    elif i > 2965 and lines[i-1].strip().startswith('except'):
        # Content of except block (20 spaces)
        if line.strip():
            lines[i] = '                    ' + line.lstrip()

# Save the fixed file
with open(filepath, 'w') as f:
    f.writelines(lines)

print("\nAfter:")
for i in range(2959, 2970):
    if i < len(lines):
        indent = len(lines[i]) - len(lines[i].lstrip())
        print(f"{i+1:4d} [{indent:2d}]: {lines[i]}", end='')

# Test compilation
print("\nTesting compilation...")
try:
    compile(open(filepath).read(), filepath, 'exec')
    print("✅ File compiles successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
    if hasattr(e, 'lineno'):
        print(f"Error at line {e.lineno}")
