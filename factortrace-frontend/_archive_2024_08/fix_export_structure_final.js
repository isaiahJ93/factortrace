const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Remove the duplicate emission fields
const duplicateFields = /\/\/ Emissions data.*?scope3_total: .*?,\s*/gs;
content = content.replace(duplicateFields, '');

// Make sure the ghg_emissions object uses the right values
const oldScope1 = 'scope1: results?.summary?.scope1_tons_co2e || 0,';
const newScope1 = 'scope1: (results?.summary?.scope1_emissions_tons_co2e || 0) / 1000,';  // Convert kg to tons

content = content.replace(oldScope1, newScope1);

// Fix scope2 and scope3
content = content.replace(
  'scope2_location: results?.summary?.scope2_location_tons_co2e || 0,',
  'scope2_location: (results?.summary?.scope2_location_emissions_tons_co2e || 0) / 1000,'
);

content = content.replace(
  'scope2_market: results?.summary?.scope2_market_tons_co2e || 0,',
  'scope2_market: (results?.summary?.scope2_market_emissions_tons_co2e || 0) / 1000,'
);

content = content.replace(
  'scope3_total: results?.summary?.scope3_tons_co2e || 0,',
  'scope3_total: (results?.summary?.scope3_emissions_tons_co2e || 0) / 1000,'
);

fs.writeFileSync(file, content);
console.log('✅ Fixed emission unit conversions (kg to tons)');
