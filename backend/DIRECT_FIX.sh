#!/bin/bash

echo "🎯 DIRECT FIX FOR ALL ISSUES"
echo "============================"

# Fix 1: Show and fix the indentation error
echo "📋 Fixing indentation error in database.py line 24..."
# Look for the connect_args line and ensure it's indented
sed -i '' '/connect_args={"check_same_thread": False}/s/^/    /' app/core/database.py

# Fix 2: Update Scope3Category import (it's in enums.py)
echo -e "\n📋 Fixing Scope3Category import..."
sed -i '' 's/from app.models.ghg_protocol_models/from app.models.enums/g' app/schemas/ghg_schemas.py
sed -i '' 's/from models.enums/from app.models.enums/g' app/schemas/ghg_schemas.py

# Fix 3: Remove duplicate lines
echo -e "\n📋 Removing duplicates..."
awk '!seen[$0]++' app/schemas/ghg_schemas.py > temp && mv temp app/schemas/ghg_schemas.py

# Fix 4: Show what we fixed
echo -e "\n✅ Fixes applied!"
echo -e "\nDatabase.py around line 24:"
sed -n '20,30p' app/core/database.py

echo -e "\nScope3Category imports in ghg_schemas.py:"
grep "import Scope3Category" app/schemas/ghg_schemas.py | head -2

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000