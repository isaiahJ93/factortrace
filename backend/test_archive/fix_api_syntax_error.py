#!/usr/bin/env python3
import re

with open('app/api/v1/api.py', 'r') as f:
    lines = f.readlines()

# Find and fix line 421
for i, line in enumerate(lines):
    if i == 420:  # Line 421 (0-indexed)
        if line.strip().endswith('["vouc'):
            lines[i] = line.rstrip() + 'her"])\n'
            print(f"Fixed line {i+1}: {lines[i].strip()}")
            break

# Write back
with open('app/api/v1/api.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed syntax error in api.py")
