#!/bin/bash

echo "🔍 SHOWING AND FIXING THE INDENTATION ERROR"
echo "==========================================="

# Show the problem
echo "📋 Current database.py lines 20-30:"
nl -ba app/core/database.py | sed -n '20,30p'

# Fix using a more direct approach
echo -e "\n🔧 Applying direct fix..."
python3 << 'EOF'
# Read the file
with open('app/core/database.py', 'r') as f:
    lines = f.readlines()

# Find line 24 (index 23) and fix it
if len(lines) > 23:
    line24 = lines[23]
    if 'connect_args' in line24 and not line24.startswith(' '):
        print(f"Found problematic line 24: {line24.strip()}")
        lines[23] = '    ' + line24.lstrip()
        print("Fixed with proper indentation")
        
        # Write back
        with open('app/core/database.py', 'w') as f:
            f.writelines(lines)
    else:
        print(f"Line 24 doesn't seem to be the connect_args line: {line24.strip()}")
        
        # Find the connect_args line
        for i, line in enumerate(lines):
            if 'connect_args' in line and not line.startswith(' '):
                print(f"Found connect_args on line {i+1}: {line.strip()}")
                lines[i] = '    ' + line.lstrip()
                with open('app/core/database.py', 'w') as f:
                    f.writelines(lines)
                print("Fixed!")
                break
EOF

# Show the fixed version
echo -e "\n✅ Fixed version (lines 20-30):"
nl -ba app/core/database.py | sed -n '20,30p'

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000