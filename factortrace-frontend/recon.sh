#!/bin/bash
echo "🔍 FACTORTRACE ARCHITECTURE RECONNAISSANCE"
echo "=========================================="

echo -e "\n📱 FRONTEND ASSETS:"
find . -type f \( -name "package.json" -o -name "tsconfig.json" \) -not -path "*/node_modules/*" -exec echo "Found: {}" \; -exec head -5 {} \;

echo -e "\n🔌 API CONFIGURATION:"
find . -type f \( -name "*.env*" -o -name "*config*.js" -o -name "*config*.ts" \) -not -path "*/node_modules/*" | grep -E "(api|backend|server)" | head -10

echo -e "\n🔐 AUTH IMPLEMENTATION:"
grep -r "JWT\|Bearer\|currentUser\|useAuth" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v node_modules | head -10

echo -e "\n📊 API SERVICE LAYER:"
find . -type f \( -name "*api*.js" -o -name "*service*.js" -o -name "*api*.ts" -o -name "*service*.ts" \) -not -path "*/node_modules/*" | head -10

echo -e "\n�� MONTE CARLO CONNECTIONS:"
grep -r "monte\|carlo\|uncertainty\|simulation" --include="*.py" app/ 2>/dev/null | grep -v __pycache__ | head -10

echo -e "\n📈 EMISSION CALCULATION CALLS:"
grep -r "calculate\|emissions\|ghg" --include="*.js" --include="*.jsx" --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v node_modules | grep -E "(fetch|axios|api)" | head -10
