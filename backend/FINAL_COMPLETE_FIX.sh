#!/bin/bash

echo "🚀 FINAL COMPLETE FIX"
echo "===================="

# Fix all settings attributes
echo "📋 Fixing all settings attributes..."

# Database URL (already done but ensure it's correct)
sed -i '' 's/settings\.SQLALCHEMY_DATABASE_URL/str(settings.database_url)/g' app/core/database.py

# Pool settings
sed -i '' 's/settings\.DB_POOL_SIZE/settings.database_pool_size/g' app/core/database.py
sed -i '' 's/settings\.DB_MAX_OVERFLOW/settings.database_max_overflow/g' app/core/database.py

# Pool timeout might not exist, so use a default value
sed -i '' 's/pool_timeout=settings\.DB_POOL_TIMEOUT/pool_timeout=30/g' app/core/database.py
sed -i '' 's/pool_timeout=settings\.database_pool_timeout/pool_timeout=30/g' app/core/database.py

# Environment and debug
sed -i '' 's/settings\.ENVIRONMENT/settings.environment/g' app/core/database.py
sed -i '' 's/settings\.DEBUG/settings.debug/g' app/core/database.py

# Show the result
echo -e "\n✅ All fixes applied. Database.py now uses:"
echo "  - str(settings.database_url)"
echo "  - settings.database_pool_size"
echo "  - settings.database_max_overflow"
echo "  - pool_timeout=30 (hardcoded)"
echo "  - settings.environment"
echo "  - settings.debug"

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000