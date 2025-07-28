#!/bin/bash
# Add debug logging to calculateEmissions (after line 386)
sed -i '' '387i\
      console.log("=== FULL API RESPONSE ===");\
      console.log("data:", JSON.stringify(data, null, 2));\
      console.log("data.breakdown:", data.breakdown);\
      console.log("======================");' src/components/emissions/EliteGHGCalculator.tsx

# Add debug to processResults (at the beginning of the function)
sed -i '' '/const processResults = /,/^  };/s/const summary = apiData.summary;/console.log("processResults received:", apiData);\n    const summary = apiData.summary;/' src/components/emissions/EliteGHGCalculator.tsx

# Add debug to prepareChartData
sed -i '' '/const prepareChartData = /,/^  };/s/const scopeData/console.log("prepareChartData categoryTotals:", Object.values(categoryTotals));\n    const scopeData/' src/components/emissions/EliteGHGCalculator.tsx
