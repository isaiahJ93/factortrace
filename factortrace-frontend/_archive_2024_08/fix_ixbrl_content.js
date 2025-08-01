const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix line 555 - change result.xhtml_content to just content
content = content.replace(
  'const ixbrlContent = result.xhtml_content;',
  'const ixbrlContent = content;'
);

// Check for any other result.xhtml_content references
content = content.replace(/result\.xhtml_content/g, 'content');

// Check for any other result. references that might break
const remainingResultRefs = content.match(/result\.\w+/g);
if (remainingResultRefs) {
  console.log('⚠️  Found remaining result references:', remainingResultRefs);
}

fs.writeFileSync(file, content);
console.log('✅ Fixed ixbrlContent reference');
