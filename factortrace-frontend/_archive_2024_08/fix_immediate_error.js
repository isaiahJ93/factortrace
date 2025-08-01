const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the styling object - it has }; instead of just }
content = content.replace(
  /dangerColor: '#ef4444'\s*\};/,
  "dangerColor: '#ef4444'\n  }"
);

fs.writeFileSync(file, content);
console.log('✅ Fixed immediate syntax error at line 61');
