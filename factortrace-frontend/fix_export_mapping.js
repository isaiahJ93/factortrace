const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find and replace the ghg_emissions section in exportData
const oldGhgSection = `ghg_emissions: {
      lei: "529900HNOAA1KXQJUQ27",
      organization: companyName || "Your Company",
      primary_nace_code: "J.62",
      reporting_period: reportingPeriod,
      scope1: 0,
      scope2_location: 0,
      scope2_market: 0,
      scope3_total: 0,
      total_emissions: 0,`;

const newGhgSection = `ghg_emissions: {
      lei: "529900HNOAA1KXQJUQ27",
      organization: companyName || "Your Company",
      primary_nace_code: "J.62",
      reporting_period: reportingPeriod,
      scope1: monteCarloResults?.summary?.scope1 || calculationResults?.totalEmissions?.scope1 || 0,
      scope2_location: monteCarloResults?.summary?.scope2Location || calculationResults?.totalEmissions?.scope2?.locationBased || 0,
      scope2_market: monteCarloResults?.summary?.scope2Market || calculationResults?.totalEmissions?.scope2?.marketBased || 0,
      scope3_total: monteCarloResults?.summary?.scope3 || calculationResults?.totalEmissions?.scope3 || 0,
      total_emissions: monteCarloResults?.summary?.total || calculationResults?.totalEmissions?.total || 0,`;

content = content.replace(oldGhgSection, newGhgSection);

fs.writeFileSync(file, content);
console.log('✅ Fixed GHG emissions mapping');
