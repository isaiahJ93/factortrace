#!/bin/bash

echo "🔧 FIXING ASYNC/SYNC POOL CONFLICT"
echo "=================================="

# Check the current database.py around line 36
echo "📋 Current engine creation code:"
sed -n '30,45p' app/core/database.py

# Fix 1: Remove poolclass if using async driver
echo -e "\n🔧 Fix 1: Removing poolclass parameter..."
sed -i '' '/poolclass=QueuePool/d' app/core/database.py

# Fix 2: Check if the URL contains asyncpg
echo -e "\n📋 Checking database URL format..."
grep -n "str(settings.database_url)" app/core/database.py | head -3

# Fix 3: Force sync driver in the URL
echo -e "\n🔧 Fix 2: Ensuring sync PostgreSQL driver..."
# Replace any asyncpg with psycopg2
sed -i '' 's/postgresql+asyncpg:/postgresql:/g' app/core/database.py
sed -i '' 's/postgresql+aiopg:/postgresql:/g' app/core/database.py

# Fix 4: Simplify the engine creation
echo -e "\n🔧 Fix 3: Simplifying engine creation..."
# Find the engine creation block and simplify it
python3 << 'EOF'
import re

with open('app/core/database.py', 'r') as f:
    content = f.read()

# Find the engine creation block
engine_pattern = r'engine = create_engine\((.*?)\)'
match = re.search(engine_pattern, content, re.DOTALL)

if match:
    # Simplify the engine creation
    new_engine = """engine = create_engine(
        str(settings.database_url),
        echo=settings.debug
    )"""
    
    content = re.sub(engine_pattern, new_engine, content, flags=re.DOTALL)
    
    with open('app/core/database.py', 'w') as f:
        f.write(content)
    
    print("✅ Simplified engine creation")
else:
    print("❌ Could not find engine creation block")
EOF

echo -e "\n✅ Fixes applied!"
echo "🚀 Starting server..."
uvicorn app.main:app --reload --port 8000