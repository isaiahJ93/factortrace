const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the specific pattern with double closing braces
content = content.replace(
  /return undefined;\s*\}\s*\}\s*return value;\s*\}\);/g,
  'return undefined;\n      }\n      return value;\n    })'
);

// Also check for any other double braces
content = content.replace(/\}\s*\}\s*return value;/g, '}\n      return value;');

fs.writeFileSync(file, content);
console.log('✅ Fixed extra closing brace');
