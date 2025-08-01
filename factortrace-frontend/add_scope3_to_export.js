const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find the exportData in exportAsIXBRL function
const exportPattern = /const exportData = \{[\s\S]*?esrs_e1_data: \{/;
const match = content.match(exportPattern);

if (match) {
  // Add scope3_breakdown before esrs_e1_data
  const insertion = `
        // Scope 3 breakdown by category
        scope3_breakdown: (() => {
          const breakdown = {};
          // Map activities to scope 3 categories
          const categoryMap = {
            'waste_landfill': 'category_5',
            'business_travel': 'category_6', 
            'employee_commuting': 'category_7',
            'upstream_electricity': 'category_3',
            'purchased_goods': 'category_1',
            'capital_goods': 'category_2',
            'fuel_energy': 'category_3',
            'upstream_transport': 'category_4'
          };
          
          results?.breakdown?.forEach((item) => {
            if (item.scope === '3') {
              const catKey = categoryMap[item.categoryId] || \`category_\${item.categoryId}\`;
              breakdown[catKey] = (breakdown[catKey] || 0) + (item.emissions_kg_co2e / 1000);
            }
          });
          
          return breakdown;
        })(),
        
        `;
  
  const newContent = content.replace('esrs_e1_data: {', insertion + 'esrs_e1_data: {');
  fs.writeFileSync(file, newContent);
  console.log('✅ Added scope3_breakdown to exportData');
} else {
  console.log('❌ Could not find exportData pattern');
}
