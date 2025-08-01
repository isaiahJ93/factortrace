const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find the exportAsIXBRL function and fix the response handling
const oldCode = `const result = await response.json();
      console.log('Export result:', result);
      
      // Handle the response - could be different formats
      let content = result.xhtml_content || result.content || result;`;

const newCode = `// The backend returns XHTML directly, not JSON
      const content = await response.text();
      console.log('Export result received, length:', content.length);`;

content = content.replace(oldCode, newCode);

// Also fix the other export functions
content = content.replace(
  'const result = await response.json();',
  'const content = await response.text();'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed XHTML response handling');
