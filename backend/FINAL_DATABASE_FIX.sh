#!/bin/bash

echo "🎯 FINAL DATABASE URL FIX"
echo "========================"
echo "Found the issue: attribute is 'database_url' (lowercase)"
echo ""

# Fix 1: Change SQLALCHEMY_DATABASE_URL to database_url
echo "📋 Fixing database.py..."
sed -i '' 's/settings\.SQLALCHEMY_DATABASE_URL/settings.database_url/g' app/core/database.py

# Fix 2: Handle the PostgresDsn type - need to convert to string
echo -e "\n📋 Converting PostgresDsn to string..."
# Change the line to handle PostgresDsn properly
sed -i '' 's/is_sqlite = settings\.database_url\.startswith/is_sqlite = str(settings.database_url).startswith/g' app/core/database.py

# Fix 3: Fix all occurrences
sed -i '' 's/settings\.database_url,/str(settings.database_url),/g' app/core/database.py

# Fix 4: Check for other settings that might need fixing
echo -e "\n📋 Checking for other settings attributes..."
if grep -q "settings\.DEBUG" app/core/database.py; then
    echo "   Fixing DEBUG attribute..."
    sed -i '' 's/settings\.DEBUG/settings.debug/g' app/core/database.py
fi

if grep -q "db_pool_size" app/core/database.py; then
    echo "   Fixing pool settings..."
    sed -i '' 's/settings\.db_pool_size/settings.database_pool_size/g' app/core/database.py
    sed -i '' 's/settings\.db_max_overflow/settings.database_max_overflow/g' app/core/database.py
    sed -i '' 's/settings\.db_pool_timeout/settings.database_pool_timeout/g' app/core/database.py
fi

# Fix 5: Show the results
echo -e "\n✅ Verification - key lines in database.py:"
grep -n "settings\." app/core/database.py | head -10

# Fix 6: Create .env file if missing
if [ ! -f .env ]; then
    echo -e "\n📋 Creating .env file..."
    cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/factortrace

# For SQLite development:
# DATABASE_URL=sqlite:///./factortrace.db

# Security
SECRET_KEY=your-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Pool
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Debug
DEBUG=true
EOF
    echo "✅ Created .env file"
fi

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000