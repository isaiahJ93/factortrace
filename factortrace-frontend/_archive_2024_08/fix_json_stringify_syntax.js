const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the broken JSON.stringify syntax
// Replace the pattern where }) is followed by });
content = content.replace(
  /return value;\s*\}\)\s*\}\);/g,
  'return value;\n      })'
);

// Also check for any other malformed patterns
content = content.replace(
  /\}\)\s*\n\s*\}\);/g,
  '})'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed JSON.stringify syntax error');
