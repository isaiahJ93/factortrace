const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find all occurrences of the component definition
const componentRegex = /const EliteGHGCalculator: React\.FC<EliteGHGCalculatorProps> = \(/g;
const matches = [...content.matchAll(componentRegex)];

console.log(`Found ${matches.length} component definitions`);

if (matches.length > 1) {
  // Keep only the FIRST one and remove the others
  for (let i = matches.length - 1; i > 0; i--) {
    const start = matches[i].index;
    // Find the end of this component (look for the next top-level const or export)
    let depth = 0;
    let end = start;
    let inString = false;
    let stringChar = '';
    
    for (let j = start; j < content.length; j++) {
      const char = content[j];
      const prevChar = j > 0 ? content[j-1] : '';
      
      // Handle strings
      if ((char === '"' || char === "'" || char === '`') && prevChar !== '\\') {
        if (!inString) {
          inString = true;
          stringChar = char;
        } else if (char === stringChar) {
          inString = false;
        }
      }
      
      if (!inString) {
        if (char === '{') depth++;
        if (char === '}') depth--;
        
        // Found the end of the component
        if (depth === 0 && j > start + 100) {
          // Look for the actual end (usually };)
          const nextSemicolon = content.indexOf('};', j);
          if (nextSemicolon !== -1 && nextSemicolon - j < 10) {
            end = nextSemicolon + 2;
          } else {
            end = j + 1;
          }
          break;
        }
      }
    }
    
    // Remove this duplicate
    console.log(`Removing duplicate component from ${start} to ${end}`);
    content = content.substring(0, start) + content.substring(end);
  }
}

// Make sure there's an export at the end
if (!content.includes('export default EliteGHGCalculator')) {
  content = content.trim() + '\n\nexport default EliteGHGCalculator;\n';
}

fs.writeFileSync(file, content);
console.log('✅ Removed duplicate components and fixed structure');
