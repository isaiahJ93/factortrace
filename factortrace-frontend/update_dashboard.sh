#!/bin/bash

# Backup first
cp src/app/dashboard/page.tsx src/app/dashboard/page.tsx.backup

# Replace setShowCalculatorModal with router.push
sed -i '' 's/setShowCalculatorModal(true)/router.push("\/calculator")/g' src/app/dashboard/page.tsx

echo "Dashboard updated! Now manually remove:"
echo "1. const [showCalculatorModal, setShowCalculatorModal] = useState(false);"
echo "2. The CalculatorModal component definition"
echo "3. <CalculatorModal ... /> at the bottom"
