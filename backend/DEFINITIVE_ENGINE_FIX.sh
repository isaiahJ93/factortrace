#!/bin/bash

echo "🎯 DEFINITIVE FIX FOR CREATE_ENGINE"
echo "==================================="

# Create a clean database.py section
echo "📋 Creating clean create_engine block..."

# Use Python to surgically fix just the engine creation
python3 << 'EOF'
with open('app/core/database.py', 'r') as f:
    content = f.read()

# Split into lines
lines = content.split('\n')

# Find the is_sqlite line (should be before engine creation)
is_sqlite_line = -1
for i, line in enumerate(lines):
    if 'is_sqlite = ' in line:
        is_sqlite_line = i
        break

# Reconstruct the file with a clean engine block
new_lines = []
skip_until_after_engine = False

for i, line in enumerate(lines):
    if 'engine = create_engine(' in line:
        # Add the clean engine block
        new_lines.append('engine = create_engine(')
        new_lines.append('    str(settings.database_url),')
        new_lines.append('    connect_args={"check_same_thread": False} if is_sqlite else {},')
        new_lines.append('    echo=settings.debug')
        new_lines.append(')')
        skip_until_after_engine = True
    elif skip_until_after_engine:
        # Skip lines until we find something that's clearly after the engine block
        if '@event.listens_for' in line or 'SessionLocal' in line or line.strip() == '' and i > is_sqlite_line + 10:
            skip_until_after_engine = False
            new_lines.append(line)
    else:
        new_lines.append(line)

# Write the fixed content
with open('app/core/database.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ Fixed create_engine block!")
EOF

# Show the result
echo -e "\n📋 Fixed database.py (showing engine creation):"
grep -B2 -A6 "engine = create_engine" app/core/database.py

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000