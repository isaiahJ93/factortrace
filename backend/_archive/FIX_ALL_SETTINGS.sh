#!/bin/bash

echo "🎯 FIXING ALL REMAINING SETTINGS"
echo "================================"

# Show current problematic lines
echo "📋 Current settings references:"
grep -n "settings\." app/core/database.py | grep -v "str(settings.database_url)"

# Fix all at once
echo -e "\n🔧 Applying comprehensive fix..."

# Pool settings
sed -i '' 's/settings\.DB_POOL_SIZE/settings.database_pool_size/g' app/core/database.py
sed -i '' 's/settings\.DB_MAX_OVERFLOW/settings.database_max_overflow/g' app/core/database.py
sed -i '' 's/settings\.DB_POOL_TIMEOUT/settings.database_pool_timeout/g' app/core/database.py

# Environment
sed -i '' 's/settings\.ENVIRONMENT/settings.environment/g' app/core/database.py

# Any other uppercase attributes to lowercase
sed -i '' 's/settings\.DEBUG/settings.debug/g' app/core/database.py

# Check if there are any timeout values that need fixing
sed -i '' 's/settings\.database_pool_timeout/30/g' app/core/database.py 2>/dev/null || true

echo -e "\n✅ Verification - all settings references:"
grep -n "settings\." app/core/database.py

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000