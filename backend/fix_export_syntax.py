#!/usr/bin/env python3

# Read the file
with open('src/components/emissions/EliteGHGCalculator.tsx', 'r') as f:
    lines = f.readlines()

# Look for the unterminated string around line 1772
for i in range(1770, min(1775, len(lines))):
    if i < len(lines):
        line = lines[i]
        # Check for unterminated strings
        if line.count("'") % 2 != 0 or (line.count('"') % 2 != 0 and '\"' not in line):
            print(f"Found unterminated string at line {i+1}: {line.strip()}")
            # Fix common issues
            if line.strip().endswith("'application/xhtml+xml\\'"):
                lines[i] = line.replace("'application/xhtml+xml\\'", "'application/xhtml+xml'")
            elif "type: '" in line and not line.strip().endswith("'"):
                lines[i] = line.rstrip() + "' });\n"

# Write back
with open('src/components/emissions/EliteGHGCalculator.tsx', 'w') as f:
    f.writelines(lines)

print("✅ Fixed syntax errors")
