const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find the exportAsIXBRL function and add emissions at root level
const oldExportData = `// Include breakdown if available
        ghg_breakdown: results?.enhancedBreakdown || [],
        esrs_e1_data: {`;

const newExportData = `// Include breakdown if available
        ghg_breakdown: results?.enhancedBreakdown || [],
        
        // Backend expects 'emissions' at root level
        emissions: {
          scope1: (results?.summary?.scope1_emissions || 0) / 1000,
          scope2: (results?.summary?.scope2_location_based || 0) / 1000,
          scope2_location: (results?.summary?.scope2_location_based || 0) / 1000,
          scope2_market: (results?.summary?.scope2_market_based || 0) / 1000,
          scope3: (results?.summary?.scope3_emissions || 0) / 1000,
          total: results?.summary?.total_emissions_tons_co2e || 0
        },
        
        esrs_e1_data: {`;

content = content.replace(oldExportData, newExportData);

fs.writeFileSync(file, content);
console.log('✅ Added emissions object at root level for backend');
