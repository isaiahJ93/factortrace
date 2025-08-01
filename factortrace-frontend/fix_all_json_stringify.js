const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix any JSON.stringify that ends with }) on a separate line
content = content.replace(
  /return value;\s*\n\s*\}\)\s*\n/g,
  'return value;\n    })\n'
);

// Add semicolon after }) if followed by code
content = content.replace(
  /\}\)\s*\n\s*if \(!response\.ok\)/g,
  '});\n    \n    if (!response.ok)'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed all JSON.stringify patterns');
