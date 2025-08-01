const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find scope3_breakdown and replace with all 15 categories
const pattern = /scope3_breakdown: \{[^}]+\}/g;
const replacement = `scope3_breakdown: {
          category_1: 1.046718,
          category_2: 200.33446,
          category_3: 0.010575,
          category_4: 0.331488,
          category_5: 0,  // Waste
          category_6: 1.715432,
          category_7: 0,  // Employee commuting
          category_8: 0,  // Upstream leased
          category_9: 0,  // Downstream transport
          category_10: 0, // Processing sold
          category_11: 0, // Use of products
          category_12: 0, // End-of-life
          category_13: 0, // Downstream leased
          category_14: 0, // Franchises
          category_15: 0  // Investments
        }`;

content = content.replace(pattern, replacement);

fs.writeFileSync(file, content);
console.log('✅ Added all 15 Scope 3 categories');
