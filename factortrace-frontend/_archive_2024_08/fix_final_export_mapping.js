const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find the ghg_emissions section in exportData
const oldGhgEmissions = `// Additional ESRS data
        primary_nace_code: "J.62", // Default to IT services
        consolidation_scope: "parent_and_subsidiaries",
        
        // Include breakdown if available
        ghg_breakdown: results?.enhancedBreakdown || [],`;

const newGhgEmissions = `// Additional ESRS data
        primary_nace_code: "J.62", // Default to IT services
        consolidation_scope: "parent_and_subsidiaries",
        
        // GHG emissions data for backend
        ghg_emissions: {
          lei: "529900HNOAA1KXQJUQ27",
          organization: companyName || "Your Company",
          primary_nace_code: "J.62",
          reporting_period: reportingPeriod,
          scope1: results?.summary?.scope1_tons_co2e || 0,
          scope2_location: results?.summary?.scope2_location_tons_co2e || 0,
          scope2_market: results?.summary?.scope2_market_tons_co2e || 0,
          scope3_total: results?.summary?.scope3_tons_co2e || 0,
          total_emissions: results?.summary?.total_emissions_tons_co2e || 0,
          ghg_breakdown: results?.ghg_breakdown || {},
          scope3_breakdown: results?.scope3_breakdown || {}
        },
        
        // Include breakdown if available
        ghg_breakdown: results?.enhancedBreakdown || [],`;

content = content.replace(oldGhgEmissions, newGhgEmissions);

fs.writeFileSync(file, content);
console.log('✅ Added proper ghg_emissions object to export data');
