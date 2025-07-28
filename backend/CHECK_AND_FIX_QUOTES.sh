#!/bin/bash

echo "🔍 CHECKING AND FIXING QUOTES"
echo "============================"

# Check ghg_schemas.py line 65
echo "📋 Current line 65 of ghg_schemas.py:"
sed -n '65p' app/schemas/ghg_schemas.py

# Fix ghg_schemas.py - remove extra quotes and add just one set
echo -e "\n🔧 Fixing ghg_schemas.py..."
# Replace the line with too many quotes
sed -i '' '65s/"""*$/"""/' app/schemas/ghg_schemas.py

# Check ghg_tables.py line 15
echo -e "\n📋 Current line 15 of ghg_tables.py:"
sed -n '15p' app/models/ghg_tables.py

# Check if it needs closing quotes
echo -e "\n📋 Checking lines 14-16 of ghg_tables.py:"
sed -n '14,16p' app/models/ghg_tables.py

# Fix by adding closing quotes on the next line if needed
sed -i '' '15a\
    """
' app/models/ghg_tables.py

echo -e "\n✅ Fixed!"
echo "🚀 Starting server..."
uvicorn app.main:app --reload --port 8000