const fs = require('fs');

const filePath = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(filePath, 'utf8');

// Check if SCOPE3_CATEGORIES is inside the component function
if (content.includes('export default function EliteGHGCalculator')) {
  // Find where the function starts
  const functionStart = content.indexOf('export default function EliteGHGCalculator');
  const firstBrace = content.indexOf('{', functionStart);
  
  // Check if SCOPE3_CATEGORIES is defined before the function
  const scope3Index = content.indexOf('const SCOPE3_CATEGORIES');
  
  if (scope3Index > firstBrace) {
    console.log('SCOPE3_CATEGORIES is inside the function - moving it outside');
    
    // Extract the SCOPE3_CATEGORIES definition
    const scope3Start = content.indexOf('const SCOPE3_CATEGORIES');
    let braceCount = 0;
    let scope3End = scope3Start;
    
    for (let i = scope3Start; i < content.length; i++) {
      if (content[i] === '{') braceCount++;
      if (content[i] === '}') braceCount--;
      if (braceCount === 0 && i > scope3Start + 10) {
        scope3End = i + 1;
        break;
      }
    }
    
    const scope3Definition = content.substring(scope3Start, scope3End) + ';\n\n';
    
    // Remove it from inside the function
    content = content.substring(0, scope3Start) + content.substring(scope3End);
    
    // Add it before the function
    content = content.substring(0, functionStart) + scope3Definition + content.substring(functionStart);
  }
}

fs.writeFileSync(filePath, content);
console.log('✅ Moved SCOPE3_CATEGORIES to global scope');
