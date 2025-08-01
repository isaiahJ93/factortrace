#!/bin/bash

# Quick fix for line 3456 syntax error
# This script uses sed to fix the specific indentation issue

echo "🔧 Quick fix for line 3456 indentation issue"

# Backup the file first
cp app/api/v1/endpoints/esrs_e1_full.py app/api/v1/endpoints/esrs_e1_full.py.backup

# Fix line 3456 - add 4 spaces to indent the description line
sed -i '' '3456s/^/    /' app/api/v1/endpoints/esrs_e1_full.py

# Also fix line 3459 if it has the same issue
sed -i '' '3459s/^description/    description/' app/api/v1/endpoints/esrs_e1_full.py

echo "✅ Applied indentation fixes"

# Test the syntax
echo "🔍 Testing Python syntax..."
python -m py_compile app/api/v1/endpoints/esrs_e1_full.py

if [ $? -eq 0 ]; then
    echo "✅ Syntax check passed! Your file is fixed!"
    echo ""
    echo "🚀 Now restart your server:"
    echo "   uvicorn app.main:app --reload"
else
    echo "❌ Syntax errors remain. Trying alternative fix..."
    
    # Restore backup and try a different approach
    cp app/api/v1/endpoints/esrs_e1_full.py.backup app/api/v1/endpoints/esrs_e1_full.py
    
    # Use Python to fix it
    python3 -c "
import sys

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Fix line 3456 (index 3455)
if len(lines) > 3455 and 'description =' in lines[3455]:
    # Add 4 more spaces to match the indentation of the line above
    lines[3455] = '    ' + lines[3455]
    print('Fixed line 3456')

# Fix line 3459 if needed
if len(lines) > 3458 and 'description =' in lines[3458] and lines[3458][0] != ' ':
    lines[3458] = '        ' + lines[3458]
    print('Fixed line 3459')

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print('✅ Applied Python-based fix')
"
    
    # Test again
    python -m py_compile app/api/v1/endpoints/esrs_e1_full.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Alternative fix worked!"
    else
        echo "❌ Still having issues. Let's see the exact problem:"
        echo ""
        echo "Lines around 3456:"
        sed -n '3450,3465p' app/api/v1/endpoints/esrs_e1_full.py | cat -n
    fi
fi