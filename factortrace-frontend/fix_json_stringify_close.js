const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the incomplete JSON.stringify closing
// Change }) to }); on line 334
content = content.replace(
  /return value;\s*\n\s*\}\)\s*\n\s*\n\s*if \(!response\.ok\)/,
  'return value;\n    });\n    \n    if (!response.ok)'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed JSON.stringify closing - added missing semicolon');
