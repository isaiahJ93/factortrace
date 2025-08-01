const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix line 334 - it should be })
// Then we need }); on the next line to close the fetch
content = content.replace(
  /return value;\s*\n\s*\}\)\);/g,
  'return value;\n    })\n    });'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed fetch closing - split })); into }) and });');
