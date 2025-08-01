const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Replace the duplicate JSON.stringify in the fetch with just dataToSend
content = content.replace(
  /body: JSON\.stringify\(exportData, \(key, value\) => \{[\s\S]*?\}\)\s*\}\);/g,
  'body: dataToSend'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed duplicate JSON.stringify - now using dataToSend variable');
