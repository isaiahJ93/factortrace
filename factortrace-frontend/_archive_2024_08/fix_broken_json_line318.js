const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the broken JSON.stringify on line 318
content = content.replace(
  /body: dataToSend => \{/g,
  'body: JSON.stringify(exportData, (key, value) => {'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed broken JSON.stringify syntax on line 318');
