#!/bin/bash

echo "🔍 DIAGNOSING QUOTE ISSUES"
echo "=========================="

# Check ghg_schemas.py around line 65
echo "📋 ghg_schemas.py lines 60-72:"
nl -ba app/schemas/ghg_schemas.py | sed -n '60,72p'

# Check ghg_tables.py around line 16
echo -e "\n📋 ghg_tables.py lines 10-20:"
nl -ba app/models/ghg_tables.py | sed -n '10,20p'

# Fix using Python for more control
echo -e "\n🔧 Applying comprehensive fix..."
python3 << 'EOF'
# Fix ghg_schemas.py
print("\n📋 Fixing ghg_schemas.py...")
with open('app/schemas/ghg_schemas.py', 'r') as f:
    content = f.read()

# Find the class definition that should contain line 65
lines = content.split('\n')

# Look for the problematic docstring around line 65
for i in range(60, min(72, len(lines))):
    if i < len(lines) and '"""' in lines[i]:
        # Check if this line has an odd number of quotes (unclosed)
        if lines[i].count('"""') % 2 != 0:
            print(f"Found unclosed docstring at line {i+1}: {lines[i]}")
            # Check next few lines for closing quotes
            found_close = False
            for j in range(i+1, min(i+10, len(lines))):
                if '"""' in lines[j]:
                    found_close = True
                    break
            
            if not found_close:
                # Add closing quotes on the same line if it's a one-liner
                if 'Query parameters' in lines[i]:
                    lines[i] = '    """Query parameters for emission factor search"""'
                    print(f"Fixed line {i+1} as one-line docstring")

with open('app/schemas/ghg_schemas.py', 'w') as f:
    f.write('\n'.join(lines))

# Fix ghg_tables.py
print("\n📋 Fixing ghg_tables.py...")
with open('app/models/ghg_tables.py', 'r') as f:
    content = f.read()

lines = content.split('\n')

# Count all """ in the file
quote_count = content.count('"""')
print(f"Total '\"\"\"' count in ghg_tables.py: {quote_count}")

if quote_count % 2 != 0:
    print("Odd number of triple quotes - need to close one")
    # Find the unclosed docstring
    in_docstring = False
    for i, line in enumerate(lines):
        if '"""' in line:
            count = line.count('"""')
            if count == 1:
                in_docstring = not in_docstring
                if in_docstring:
                    print(f"Docstring opens at line {i+1}")
                else:
                    print(f"Docstring closes at line {i+1}")
    
    # If we're still in a docstring, we need to close it
    if in_docstring:
        # Find a good place to close it (around line 16-20)
        for i in range(15, min(25, len(lines))):
            if lines[i].strip() == '':
                lines[i] = '    """'
                print(f"Added closing quotes at line {i+1}")
                break
        else:
            # If no empty line, add after line 16
            lines.insert(16, '    """')
            print("Inserted closing quotes at line 17Mackay93
            

with open('app/models/ghg_tables.py', 'w') as f:
    f.write('\n'.join(lines))

print("\n✅ Fixes applied!")
EOF

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000