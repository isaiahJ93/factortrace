#!/bin/bash

echo "🎯 FIXING ENTIRE CREATE_ENGINE BLOCK"
echo "==================================="

# Fix using Python to handle the entire block properly
python3 << 'EOF'
import re

with open('app/core/database.py', 'r') as f:
    content = f.read()

# Find and fix the create_engine block
lines = content.split('\n')
fixed_lines = []
in_engine_block = False
indent_level = 0

for i, line in enumerate(lines):
    # Detect start of create_engine
    if 'engine = create_engine(' in line or (i > 0 and 'create_engine(' in lines[i-1]):
        in_engine_block = True
        # Determine indent level from this line
        indent_level = len(line) - len(line.lstrip())
        fixed_lines.append(line)
        continue
    
    # If we're in the engine block
    if in_engine_block:
        stripped = line.strip()
        
        # If line has content and no proper indentation
        if stripped and not line.startswith(' '):
            # Add proper indentation (4 spaces more than the engine = line)
            fixed_line = ' ' * (indent_level + 4) + stripped
            fixed_lines.append(fixed_line)
            print(f"Fixed line {i+1}: {stripped}")
        else:
            fixed_lines.append(line)
        
        # Check if we're done (closing parenthesis)
        if ')' in line and not line.rstrip().endswith(','):
            in_engine_block = False
    else:
        fixed_lines.append(line)

# Write back
with open('app/core/database.py', 'w') as f:
    f.write('\n'.join(fixed_lines))

print("\n✅ Fixed entire create_engine block!")
EOF

# Show the result
echo -e "\n📋 Fixed create_engine block:"
grep -A 10 "engine = create_engine" app/core/database.py | head -15

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000