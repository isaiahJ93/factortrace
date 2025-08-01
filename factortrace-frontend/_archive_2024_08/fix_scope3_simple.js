const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Replace the scope3_breakdown with a simpler version
const oldPattern = /scope3_breakdown: \(\(\) => \{[\s\S]*?\}\)\(\),/;

const newSimple = `scope3_breakdown: (() => {
          const breakdown = {};
          
          // Just get the Scope 3 items from ghg_breakdown
          const scope3Items = results?.ghg_breakdown?.filter(item => item.scope === '3') || [];
          
          // Category mapping
          const categoryMap = {
            'waste_landfill': 5,
            'plastic_packaging': 1,
            'road_freight': 4,
            'office_paper': 1,
            'upstream_electricity': 3
          };
          
          scope3Items.forEach(item => {
            const catNum = categoryMap[item.activity_type];
            if (catNum) {
              const key = \`category_\${catNum}\`;
              breakdown[key] = (breakdown[key] || 0) + (item.emissions_kg_co2e / 1000);
            }
          });
          
          // Ensure we have values for the main categories from your data
          breakdown['category_1'] = breakdown['category_1'] || 0;  // Purchased goods
          breakdown['category_3'] = breakdown['category_3'] || 0;  // Fuel/energy  
          breakdown['category_4'] = breakdown['category_4'] || 0;  // Transport
          breakdown['category_5'] = breakdown['category_5'] || 0;  // Waste
          
          return breakdown;
        })(),`;

content = content.replace(oldPattern, newSimple);

fs.writeFileSync(file, content);
console.log('✅ Simplified scope3_breakdown mapping');
