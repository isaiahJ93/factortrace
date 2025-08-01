const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find and update the scope3_breakdown mapping
const oldPattern = /scope3_breakdown: \(\(\) => {[\s\S]*?\}\)\(\),/;

const newScope3 = `scope3_breakdown: (() => {
            const breakdown = {};
            const scope3Categories = [
              'purchased_goods', 'capital_goods', 'fuel_energy', 'upstream_transport',
              'waste', 'business_travel', 'employee_commuting', 'upstream_leased',
              'downstream_transport', 'processing_sold', 'use_of_products', 'end_of_life',
              'downstream_leased', 'franchises', 'investments'
            ];
            
            // Map frontend categories to backend format
            results?.breakdown?.forEach((item) => {
              if (item.scope === '3' && item.categoryId) {
                const categoryIndex = scope3Categories.indexOf(item.categoryId) + 1;
                if (categoryIndex > 0) {
                  // Backend expects 'category_1', 'category_2', etc.
                  breakdown[\`category_\${categoryIndex}\`] = item.emissions_kg_co2e / 1000;
                }
              }
            });
            
            // Ensure all 15 categories exist (even if 0)
            for (let i = 1; i <= 15; i++) {
              if (!breakdown[\`category_\${i}\`]) {
                breakdown[\`category_\${i}\`] = 0;
              }
            }
            
            return breakdown;
          })(),`;

// First check if scope3_breakdown already exists
if (content.includes('scope3_breakdown:')) {
  // Replace existing
  content = content.replace(oldPattern, newScope3);
} else {
  // Add it after scope3_total
  content = content.replace(
    /scope3_total: \(results\?\.summary\?\.scope3_emissions \|\| 0\) \/ 1000,/,
    `scope3_total: (results?.summary?.scope3_emissions || 0) / 1000,\n          ${newScope3}`
  );
}

fs.writeFileSync(file, content);
console.log('✅ Fixed scope3_breakdown format to match backend expectations');
