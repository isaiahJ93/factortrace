const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Replace the scope3_breakdown function with a debug version
const oldPattern = /scope3_breakdown: \(\(\) => \{[\s\S]*?\}\)\(\),/;

const newDebugVersion = `scope3_breakdown: (() => {
          const breakdown = {};
          console.log('Debug: Building scope3_breakdown');
          console.log('Results breakdown:', results?.breakdown);
          
          // Direct category mapping based on your activities
          const categoryMap = {
            'waste_landfill': 5,  // Category 5: Waste
            'plastic_packaging': 1,  // Category 1: Purchased goods
            'office_paper': 1,  // Category 1: Purchased goods  
            'upstream_electricity': 3,  // Category 3: Fuel/energy
            'machinery': 2,  // Category 2: Capital goods
            'diesel_fleet': null,  // This is Scope 1, not 3
            'natural_gas_stationary': null,  // This is Scope 1
            'electricity_grid': null,  // This is Scope 2
            'district_heating': null  // This is Scope 2
          };
          
          results?.breakdown?.forEach((item) => {
            console.log('Processing item:', item.activity_type, 'scope:', item.scope);
            if (item.scope === '3' && item.activity_type) {
              const categoryNum = categoryMap[item.activity_type];
              if (categoryNum) {
                const catKey = \`category_\${categoryNum}\`;
                breakdown[catKey] = (breakdown[catKey] || 0) + (item.emissions_kg_co2e / 1000);
                console.log('Added to', catKey, ':', item.emissions_kg_co2e / 1000);
              }
            }
          });
          
          console.log('Final scope3_breakdown:', breakdown);
          return breakdown;
        })(),`;

content = content.replace(oldPattern, newDebugVersion);

fs.writeFileSync(file, content);
console.log('✅ Added debug version of scope3_breakdown');
