#!/bin/bash

echo "🔧 FIXING IF/ELSE INDENTATION"
echo "============================"

# Show current structure
echo "📋 Current database.py lines 15-30:"
nl -ba app/core/database.py | sed -n '15,30p'

# Fix the indentation after if statement
echo -e "\n🔧 Fixing indentation..."
python3 << 'EOF'
with open('app/core/database.py', 'r') as f:
    lines = f.readlines()

# Fix the if/else block structure
fixed_lines = []
for i, line in enumerate(lines):
    if i == 17 and 'if is_sqlite:' in line:  # Line 18 (index 17)
        fixed_lines.append(line)
        # Make sure next non-empty lines are indented
        continue
    elif i > 17 and i < 25:  # Lines after if statement
        if line.strip() and not line.startswith(' '):
            # Add indentation
            fixed_lines.append('    ' + line)
            print(f"Fixed indentation on line {i+1}")
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

with open('app/core/database.py', 'w') as f:
    f.writelines(fixed_lines)

print("\n✅ Fixed if/else indentation!")
EOF

# Show the fixed version
echo -e "\n📋 Fixed database.py lines 15-30:"
nl -ba app/core/database.py | sed -n '15,30p'

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000