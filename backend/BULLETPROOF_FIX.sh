#!/bin/bash

echo "🔍 DIAGNOSING AND FIXING INDENTATION ERROR"
echo "=========================================="

# Show the exact error line
echo "📋 The error is on line 24. Let's see it:"
echo "Line 24: $(sed -n '24p' app/core/database.py)"

# Show context
echo -e "\n📋 Context (lines 20-30):"
awk 'NR>=20 && NR<=30 {printf "%2d: %s\n", NR, $0}' app/core/database.py

# Check if line 24 starts with spaces
echo -e "\n🔍 Checking line 24 indentation:"
if [[ $(sed -n '24p' app/core/database.py) =~ ^[[:space:]] ]]; then
    echo "Line 24 IS indented (starts with spaces)"
else
    echo "Line 24 is NOT indented (starts at column 0)"
fi

# Fix it
echo -e "\n🔧 Fixing..."
# Use awk to fix line 24
awk 'NR==24 && !/^[[:space:]]/ {print "    " $0; next} {print}' app/core/database.py > temp_db.py && mv temp_db.py app/core/database.py

echo -e "\n✅ Fixed! New line 24:"
echo "Line 24: $(sed -n '24p' app/core/database.py)"

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000