const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find the broken import line
const brokenLine = content.indexOf('eChart, Line, BarChart, Bar, XAxis, YAxis');
if (brokenLine > -1) {
  // Find where it should end (at the next line that starts properly)
  const endOfBroken = content.indexOf('\n// Emission calculation constants', brokenLine);
  
  // Remove the broken imports from the middle
  if (endOfBroken > -1) {
    content = content.substring(0, brokenLine) + content.substring(endOfBroken);
  }
  
  // Clean up any duplicate semicolons or braces
  content = content.replace(/};\s*};/g, '};');
  content = content.replace(/}\s*};/g, '};');
  
  console.log('✅ Removed broken import statements from middle of file');
} else {
  console.log('❌ Could not find broken import line');
}

fs.writeFileSync(file, content);
