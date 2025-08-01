const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the pattern where }) should be ))
// Look for "return value;" followed by }) and then });
content = content.replace(
  /return value;\s*\n\s*\}\)\s*\n\s*\}\);/g,
  'return value;\n    })\n    });'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed JSON.stringify closing - }) changed to ))');
