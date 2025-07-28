#!/bin/bash

# Check current setup
echo "Current API_URL setup:"
grep -n "API_URL" src/components/emissions/EliteGHGCalculator.tsx

# Fix to match dashboard (port 8001, no /api/v1 in URL)
sed -i '' 's|const API_URL = .*|const API_URL = process.env.NEXT_PUBLIC_API_URL || '\''http://localhost:8001'\'';|g' src/components/emissions/EliteGHGCalculator.tsx

# Update the fetch to include /api/v1
sed -i '' 's|`${API_URL}/calculate-with-monte-carlo`|`${API_URL}/api/v1/calculate-with-monte-carlo`|g' src/components/emissions/EliteGHGCalculator.tsx

echo ""
echo "Updated to:"
grep -A1 "API_URL" src/components/emissions/EliteGHGCalculator.tsx
grep "calculate-with-monte-carlo" src/components/emissions/EliteGHGCalculator.tsx
