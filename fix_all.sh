#!/bin/bash

echo "🔧 Fixing FactorTrace Setup..."

# Fix backend syntax error
cd ~/Documents/Scope3Tool/backend
echo "Fixing models/__init__.py syntax error..."
# Remove the ] character
sed -i '' 's/]from/from/g' app/models/__init__.py

# Show the fixed file
echo "Models __init__.py now contains:"
cat app/models/__init__.py

echo ""
echo "✅ Backend fixed!"
echo ""
echo "Next steps:"
echo "1. In Terminal 1: cd ~/Documents/Scope3Tool/backend && uvicorn app.main:app --reload --port 8001"
echo "2. In Terminal 2: cd ~/Documents/Scope3Tool/backend && python scripts/seed_emission_factors_direct.py"
echo "3. In Terminal 3: cd ~/Documents/Scope3Tool/frontend && npm run dev"
