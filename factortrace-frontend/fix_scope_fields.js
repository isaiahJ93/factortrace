const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Fix scope3 field name in emissions object
content = content.replace(
  /scope3: \(results\?\.summary\?\.scope3_emissions \|\| 0\) \/ 1000/g,
  'scope3_total: (results?.summary?.scope3_emissions || 0) / 1000'
);

// Also update in ghg_emissions object
content = content.replace(
  'scope3_total: (results?.summary?.scope3_emissions || 0) / 1000,  // Convert kg to tons',
  'scope3_total: (results?.summary?.scope3_emissions || 0) / 1000,  // Convert kg to tons'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed scope3 field name to scope3_total');
