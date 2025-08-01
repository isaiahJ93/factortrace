const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the console.log to use 'results' instead of 'calculationResults'
content = content.replace(
  "console.log('Calculation Results:', calculationResults);",
  "console.log('Results state:', results);"
);

// Also fix the reference error
content = content.replace(
  "console.log('Monte Carlo Results:', monteCarloResults);",
  "console.log('Results breakdown:', results?.enhancedBreakdown);"
);

fs.writeFileSync(file, content);
console.log('✅ Fixed debug logging to use correct variable names');
