const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
const content = fs.readFileSync(file, 'utf8');

// Split into lines
const lines = content.split('\n');

// Find and fix line 334 (index 333)
if (lines[333] && lines[333].trim() === '})') {
  lines[333] = '    });';
  console.log('Fixed line 334: changed }) to });');
} else {
  console.log('Line 334 content:', lines[333]);
  
  // Try to find the pattern anywhere
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === '})' && 
        i + 2 < lines.length && 
        lines[i + 2].includes('if (!response.ok)')) {
      lines[i] = lines[i].replace(')', ');');
      console.log(`Fixed line ${i + 1}: added semicolon`);
      break;
    }
  }
}

// Write back
fs.writeFileSync(file, lines.join('\n'));
console.log('✅ Fixed line 334 semicolon issue');
