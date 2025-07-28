import re

# Read the file
with open('factortrace/factor_loader.py', 'r') as f:
    lines = f.readlines()

# Fix line by line
fixed_lines = []
for i, line in enumerate(lines):
    # Fix unterminated strings ending with FIXME
    if '"FIXME' in line and not line.strip().endswith('"'):
        line = line.rstrip() + '"\n'
        print(f"Fixed line {i+1}: {line.strip()}")
    fixed_lines.append(line)

# Write it back
with open('factortrace/factor_loader.py', 'w') as f:
    f.writelines(fixed_lines)

print("Done fixing strings!")
