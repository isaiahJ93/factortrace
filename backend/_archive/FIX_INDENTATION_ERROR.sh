#!/bin/bash

echo "🔧 FIXING INDENTATION ERROR IN DATABASE.PY"
echo "========================================="

# Show the problematic area
echo "📋 Current database.py around line 24:"
sed -n '20,30p' app/core/database.py

# Fix the indentation error
echo -e "\n🔧 Fixing indentation..."
python3 << 'EOF'
with open('app/core/database.py', 'r') as f:
    lines = f.readlines()

# Find and fix the indentation issue around line 24
fixed_lines = []
for i, line in enumerate(lines):
    # Check if this line has bad indentation
    if i > 0 and line.strip() and not line[0].isspace() and lines[i-1].rstrip().endswith(','):
        # Previous line ended with comma but this line isn't indented
        fixed_lines.append('    ' + line)
    elif 'connect_args=' in line and line[0] != ' ':
        # This line should be indented
        fixed_lines.append('    ' + line)
    else:
        fixed_lines.append(line)

with open('app/core/database.py', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Fixed indentation")
EOF

# Also fix the Scope3Category import issue
echo -e "\n🔧 Fixing Scope3Category import (from enums.py)..."
sed -i '' 's/from app.models.ghg_protocol_models import Scope3Category/from app.models.enums import Scope3Category/g' app/schemas/ghg_schemas.py

# Clean up any duplicate imports
echo -e "\n🔧 Removing duplicate imports..."
awk '!seen[$0]++' app/schemas/ghg_schemas.py > app/schemas/ghg_schemas.tmp && mv app/schemas/ghg_schemas.tmp app/schemas/ghg_schemas.py

echo -e "\n✅ All fixes applied!"
echo -e "\n📋 Checking database.py line 24:"
sed -n '22,26p' app/core/database.py

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000