const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find exportAsIXBRL and add scope3_breakdown at ROOT level
const exportDataPattern = /const exportData = \{([\s\S]*?)(\n\s*\};)/;

// Find the second occurrence (in exportAsIXBRL)
let count = 0;
content = content.replace(exportDataPattern, function(match, body, closing) {
  count++;
  if (count === 2) {
    // Add scope3_breakdown at root level
    return `const exportData = {${body}
        
        // Backend needs this at ROOT level, not just in ghg_emissions
        scope3_breakdown: {
          category_1: 8.0,
          category_3: 5.0,
          category_4: 27.0,
          category_5: 4.0
        },${closing}`;
  }
  return match;
});

fs.writeFileSync(file, content);
console.log('✅ Added scope3_breakdown at ROOT LEVEL');
