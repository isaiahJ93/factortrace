#!/bin/bash

echo "🏆 VICTORY FIX - FINAL SOLUTION"
echo "==============================="

# Fix all issues in one go
echo "📋 Applying all fixes..."

# 1. Add Scope3Category import to ghg_schemas.py (at line 5)
echo -e "\n1️⃣ Adding Scope3Category import to ghg_schemas.py..."
if ! grep -q "from app.models.ghg_protocol_models import Scope3Category" app/schemas/ghg_schemas.py; then
    sed -i '' '5i\
from app.models.ghg_protocol_models import Scope3Category, CalculationMethod
' app/schemas/ghg_schemas.py
fi

# 2. Ensure ghg_tables.py also has the import
echo -e "\n2️⃣ Ensuring ghg_tables.py has imports..."
if ! grep -q "from app.schemas.ghg_schemas import Scope3Category" app/models/ghg_tables.py; then
    sed -i '' '/from app.core.database import Base/a\
from app.schemas.ghg_schemas import Scope3Category, CalculationMethod
' app/models/ghg_tables.py
fi

# 3. Remove any duplicate imports
echo -e "\n3️⃣ Removing duplicate imports..."
for file in app/schemas/ghg_schemas.py app/models/ghg_tables.py; do
    awk '!seen[$0]++' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
done

# 4. Show results
echo -e "\n✅ All fixes applied!"
echo -e "\n📋 ghg_schemas.py imports:"
head -10 app/schemas/ghg_schemas.py | grep "import"

echo -e "\n📋 ghg_tables.py imports:"
head -20 app/models/ghg_tables.py | grep "import"

echo -e "\n🚀 STARTING SERVER..."
echo "====================="
uvicorn app.main:app --reload --port 8000