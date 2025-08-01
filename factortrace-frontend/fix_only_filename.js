const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Restore any broken comments
content = content.replace(/\/\/ result\./g, 'result.');

// Now fix ONLY the download filename line around line 1814
content = content.replace(
  /a\.download = result\.filename \|\| `ESRS_E1_Report/,
  'a.download = `ESRS_E1_Report'
);

// If there are any result references after we changed to content, fix them
content = content.replace(
  'console.log(\'Export result:\', result);',
  'console.log(\'Export result received, length:\', content.length);'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed only the necessary parts');
