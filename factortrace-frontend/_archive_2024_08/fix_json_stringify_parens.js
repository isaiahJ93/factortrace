const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the JSON.stringify closing - needs })) not })
content = content.replace(
  /return value;\s*\n\s*\}\);/g,
  'return value;\n    })),'
);

// If there's already a }); after it, change to just });
content = content.replace(
  /\}\)\),\s*\n\s*\}\);/g,
  '})),\n    });'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed JSON.stringify closing parentheses');
