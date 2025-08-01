const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the fetch structure - the if statement is inside the fetch options!
content = content.replace(
  /\}\)\),\s*\n\s*\n\s*if \(!response\.ok\)/g,
  '})\n    });\n    \n    if (!response.ok)'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed - moved if statement outside fetch options');
