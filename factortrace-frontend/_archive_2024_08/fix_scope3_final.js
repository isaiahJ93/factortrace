const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find where scope3_breakdown is in exportData
const exportDataSection = content.match(/const exportData = \{[\s\S]*?\};/g);
if (exportDataSection && exportDataSection.length > 1) {
  // Find the second exportData (in exportAsIXBRL)
  const secondExportData = exportDataSection[1];
  
  // Replace just the scope3_breakdown line
  const newExportData = secondExportData.replace(
    /scope3_breakdown: .*?,/,
    `scope3_breakdown: (() => {
          const breakdown = {};
          
          // Use ghg_breakdown from the same exportData object
          const items = results?.enhancedBreakdown || [];
          
          // Category mapping
          const categoryMap = {
            'waste_landfill': 5,
            'plastic_packaging': 1,
            'road_freight': 4,
            'office_paper': 1,
            'upstream_electricity': 3
          };
          
          items.forEach(item => {
            if (item.scope === '3' && item.activity_type) {
              const catNum = categoryMap[item.activity_type];
              if (catNum) {
                const key = \`category_\${catNum}\`;
                breakdown[key] = (breakdown[key] || 0) + (item.emissions_kg_co2e / 1000);
              }
            }
          });
          
          return breakdown;
        })(),`
  );
  
  // Replace in content
  content = content.replace(exportDataSection[1], newExportData);
  
  fs.writeFileSync(file, content);
  console.log('✅ Fixed scope3_breakdown to use enhancedBreakdown');
} else {
  console.log('❌ Could not find exportData sections');
}
