const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix the missing closing for fetch
content = content.replace(
  /body: dataToSend\s*\n\s*\n\s*if \(!response\.ok\)/g,
  'body: dataToSend\n    });\n    \n    if (!response.ok)'
);

// Also fix any other similar patterns
content = content.replace(
  /body: dataToSend\s*\n\s*if \(!response\.ok\)/g,
  'body: dataToSend\n    });\n    \n    if (!response.ok)'
);

fs.writeFileSync(file, content);
console.log('✅ Added missing }); after body: dataToSend');
