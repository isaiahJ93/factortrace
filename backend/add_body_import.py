#!/usr/bin/env python3

# Read the file
with open('app/api/v1/api.py', 'r') as f:
    lines = f.readlines()

# Find and update the fastapi import line
for i, line in enumerate(lines):
    if line.startswith('from fastapi import'):
        if 'Body' not in line:
            # Add Body to the import
            lines[i] = line.rstrip() + ', Body\n'
            print(f"✅ Added Body to line {i+1}")
            break

# Write back
with open('app/api/v1/api.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed Body import")
