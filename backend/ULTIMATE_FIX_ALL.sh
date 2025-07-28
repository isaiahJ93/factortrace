#!/bin/bash

echo "🚀 ULTIMATE FIX - CRUSHING ALL BUGS"
echo "==================================="

# Fix 1: Remove poolclass line completely
echo "📋 Fix 1: Removing poolclass line entirely..."
sed -i '' '/poolclass=QueuePool/d' app/core/database.py

# Fix 2: Fix DATABASE_URL in session.py
echo -e "\n📋 Fix 2: Fixing DATABASE_URL in session.py..."
sed -i '' 's/settings\.DATABASE_URL/str(settings.database_url)/g' app/db/session.py

# Fix 3: Fix Scope3Category import in ghg_tables.py
echo -e "\n📋 Fix 3: Adding Scope3Category import to ghg_tables.py..."
# Add import after other imports
sed -i '' '/from app.core.database import Base/a\
from app.schemas.ghg_schemas import Scope3Category, CalculationMethod
' app/models/ghg_tables.py

# Fix 4: Fix the weird backend.app import
echo -e "\n📋 Fix 4: Fixing incorrect import path..."
sed -i '' 's/from backend.app.models.emission/from app.models.emission/g' app/models/__init__.py

# Fix 5: Check if there are more DATABASE_URL references
echo -e "\n📋 Fix 5: Finding all DATABASE_URL references..."
grep -r "DATABASE_URL" app/ --include="*.py" | grep -v "__pycache__" | while read line; do
    file=$(echo "$line" | cut -d: -f1)
    echo "   Fixing: $file"
    sed -i '' 's/settings\.DATABASE_URL/str(settings.database_url)/g' "$file"
done

# Fix 6: Clean up any remaining pool parameters
echo -e "\n📋 Fix 6: Cleaning up pool parameters..."
sed -i '' '/pool_size=/d; /max_overflow=/d; /pool_timeout=/d; /pool_pre_ping=/d' app/core/database.py

echo -e "\n✅ ALL FIXES APPLIED!"
echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000