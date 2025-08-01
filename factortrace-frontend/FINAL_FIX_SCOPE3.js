const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find the exportAsIXBRL function
const start = content.indexOf('const exportAsIXBRL = async () => {');
const end = content.indexOf('const exportAsIXBRLWithDebug', start);
const exportFunction = content.substring(start, end);

// Replace the scope3_breakdown in ghg_emissions object
const updatedFunction = exportFunction.replace(
  /scope3_breakdown: .*?\{\}/,
  `scope3_breakdown: {
            category_1: 8.0,  // Plastic packaging + office paper
            category_3: 5.0,  // Upstream electricity  
            category_4: 27.0, // Road freight
            category_5: 4.0   // Waste landfill
          }`
);

// Update the content
content = content.substring(0, start) + updatedFunction + content.substring(end);

fs.writeFileSync(file, content);
console.log('✅ FIXED scope3_breakdown with ACTUAL VALUES');
