const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find the specific pattern and fix it
// The JSON.stringify should end with }) not with extra });
const lines = content.split('\n');

// Find the line with the extra });
for (let i = 0; i < lines.length; i++) {
  // Look for the pattern where }) is on one line and }); on the next
  if (i > 0 && lines[i-1].trim() === '})' && lines[i].trim() === '});') {
    // Check if the next few lines have if (!response.ok)
    let found = false;
    for (let j = i+1; j < i+5 && j < lines.length; j++) {
      if (lines[j].includes('if (!response.ok)')) {
        found = true;
        break;
      }
    }
    if (found) {
      console.log(`Found extra }); at line ${i+1}, removing it`);
      lines[i] = ''; // Remove the extra });
      break;
    }
  }
}

content = lines.join('\n');
fs.writeFileSync(file, content);
console.log('✅ Fixed JSON.stringify ending syntax');
