#!/bin/bash

echo "🔍 CHECK AND FIX DATABASE URL"
echo "============================="

# Show what we found in config.py
echo "📋 From config.py, the database URL field is:"
grep -A2 -B2 "database.*url" app/core/config.py | grep -v "^--"

echo -e "\n📋 Current error line in database.py:"
grep -n "SQLALCHEMY_DATABASE_URL" app/core/database.py

echo -e "\n🔧 The fix is: database_url (lowercase) and needs str() conversion"
echo "Because PostgresDsn type needs to be converted to string"

# Apply the fix
echo -e "\n📋 Applying fix..."
sed -i '' 's/settings\.SQLALCHEMY_DATABASE_URL/str(settings.database_url)/g' app/core/database.py

echo -e "\n✅ Fixed! New lines:"
grep -n "database_url" app/core/database.py

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000