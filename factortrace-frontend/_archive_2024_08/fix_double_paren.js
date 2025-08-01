const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
const content = fs.readFileSync(file, 'utf8');

// Fix line 334 - it needs })) not just })
const fixed = content.replace(
  /return value;\s*\n\s*\}\);\s*\n\s*\n\s*if \(!response\.ok\)/g,
  'return value;\n    }));\n    \n    if (!response.ok)'
);

// Also try without semicolon pattern
const fixed2 = fixed.replace(
  /return value;\s*\n\s*\}\)\s*\n\s*\n\s*if \(!response\.ok\)/g,
  'return value;\n    }));\n    \n    if (!response.ok)'
);

fs.writeFileSync(file, fixed2);
console.log('✅ Fixed - added double closing parentheses'));
