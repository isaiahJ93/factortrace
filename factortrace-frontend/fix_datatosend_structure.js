const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the dataToSend structure
content = content.replace(
  /\}\)\),\s*\n\s*console\.log\('=== DATA BEING SENT TO BACKEND ==='\);/g,
  '});\n      console.log(\'=== DATA BEING SENT TO BACKEND ===\');'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed dataToSend structure - changed })), to });');
