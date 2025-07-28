#!/bin/bash

echo "🔧 FIXING UNTERMINATED TRIPLE-QUOTED STRINGS"
echo "==========================================="

# Fix 1: ghg_schemas.py line 65
echo "📋 Fixing ghg_schemas.py..."
# Check line 65
echo "Line 65 of ghg_schemas.py:"
sed -n '65p' app/schemas/ghg_schemas.py

# Add closing triple quotes after line 65
sed -i '' '65a\
    """
' app/schemas/ghg_schemas.py

# Fix 2: ghg_tables.py line 15
echo -e "\n📋 Fixing ghg_tables.py..."
# Check line 15
echo "Line 15 of ghg_tables.py:"
sed -n '15p' app/models/ghg_tables.py

# Add closing triple quotes after line 15  
sed -i '' '15a\
"""
' app/models/ghg_tables.py

echo -e "\n✅ Fixed triple-quoted strings!"
echo "🚀 Starting server..."
uvicorn app.main:app --reload --port 8000