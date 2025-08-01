const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Update exportData to map results correctly
const exportSection = `const exportData = {
        organization: companyName || 'Test Organization',
        lei: "529900HNOAA1KXQJUQ27", // You should get this from company settings
        reporting_period: parseInt(reportingPeriod) || new Date().getFullYear(),
        force_generation: true,
        
        // Emissions data in tons
        total_emissions: (results?.totalEmissions?.total || 0) / 1000,
        scope1: (results?.totalEmissions?.scope1 || 0) / 1000,
        scope2_location: (results?.totalEmissions?.scope2 || 0) / 1000,
        scope2_market: (results?.totalEmissions?.scope2 || 0) / 1000, // Same as location for now
        scope3_total: (results?.totalEmissions?.scope3 || 0) / 1000,`;

const newExportSection = `const exportData = {
        organization: companyName || 'Test Organization',
        lei: "529900HNOAA1KXQJUQ27", // You should get this from company settings
        reporting_period: parseInt(reportingPeriod) || new Date().getFullYear(),
        force_generation: true,
        
        // Emissions data (check results structure)
        total_emissions: results?.summary?.total_emissions_tons_co2e || results?.totalEmissions?.total || 0,
        scope1: results?.summary?.scope1_tons_co2e || results?.totalEmissions?.scope1 || 0,
        scope2_location: results?.summary?.scope2_location_tons_co2e || results?.totalEmissions?.scope2 || 0,
        scope2_market: results?.summary?.scope2_market_tons_co2e || results?.totalEmissions?.scope2 || 0,
        scope3_total: results?.summary?.scope3_tons_co2e || results?.totalEmissions?.scope3 || 0,`;

content = content.replace(exportSection, newExportSection);

fs.writeFileSync(file, content);
console.log('✅ Fixed export to handle both possible result structures');
