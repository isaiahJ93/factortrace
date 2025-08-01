const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Replace the ghg_emissions object with correct field names and conversions
const oldGhgEmissions = /scope1: \(results\?\.summary\?\.scope1_emissions_tons_co2e.*?\|\| 0\) \/ 1000,/;
const newScope1 = 'scope1: (results?.summary?.scope1_emissions || 0) / 1000,  // Convert kg to tons';

content = content.replace(oldGhgEmissions, newScope1);

// Fix scope2_location
content = content.replace(
  /scope2_location: \(results\?\.summary\?\.scope2_location_emissions_tons_co2e.*?\|\| 0\) \/ 1000,/,
  'scope2_location: (results?.summary?.scope2_location_based || 0) / 1000,  // Convert kg to tons'
);

// Fix scope2_market
content = content.replace(
  /scope2_market: \(results\?\.summary\?\.scope2_market_emissions_tons_co2e.*?\|\| 0\) \/ 1000,/,
  'scope2_market: (results?.summary?.scope2_market_based || 0) / 1000,  // Convert kg to tons'
);

// Fix scope3
content = content.replace(
  /scope3_total: \(results\?\.summary\?\.scope3_emissions_tons_co2e.*?\|\| 0\) \/ 1000,/,
  'scope3_total: (results?.summary?.scope3_emissions || 0) / 1000,  // Convert kg to tons'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed all scope mappings to use correct API field names');
