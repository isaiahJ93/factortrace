#!/bin/bash

echo "🔧 FIXING ALL INDENTATION ERRORS IN CREATE_ENGINE BLOCK"
echo "====================================================="

# Show the problem area
echo "📋 Current database.py lines 20-35:"
sed -n '20,35p' app/core/database.py | cat -n

# Fix all lines that need indentation in the create_engine block
echo -e "\n🔧 Fixing all unindented lines..."
python3 << 'EOF'
with open('app/core/database.py', 'r') as f:
    lines = f.readlines()

# Fix lines that should be indented within create_engine
fixed = False
for i in range(len(lines)):
    line = lines[i]
    # Check if this line should be indented but isn't
    if i >= 23 and i <= 30:  # Lines 24-31 (the create_engine block)
        if line.strip() and not line.startswith(' ') and 'engine =' not in line:
            lines[i] = '    ' + line
            print(f"Fixed line {i+1}: {line.strip()}")
            fixed = True

if fixed:
    with open('app/core/database.py', 'w') as f:
        f.writelines(lines)
    print("\n✅ Fixed all indentation issues!")
else:
    print("No fixes needed")
EOF

# Show the fixed version
echo -e "\n✅ Fixed version (lines 20-35):"
sed -n '20,35p' app/core/database.py | cat -n

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000