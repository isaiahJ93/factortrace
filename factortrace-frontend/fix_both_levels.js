const fs = require('fs');
const file = 'src/components/emissions/EliteGHGCalculator.tsx';
let content = fs.readFileSync(file, 'utf8');

// Find where we build exportData
const exportDataPattern = /const exportData = {[\s\S]*?};/;

// Add emissions data at BOTH top level AND in ghg_emissions
const newExportData = `const exportData = {
        organization: companyName || 'Test Organization',
        lei: "529900HNOAA1KXQJUQ27",
        reporting_period: parseInt(reportingPeriod) || new Date().getFullYear(),
        force_generation: true,
        
        // Top-level emissions (what backend might expect)
        scope1: (results?.summary?.scope1_emissions || 0) / 1000,
        scope2_location: (results?.summary?.scope2_location_based || 0) / 1000,
        scope2_market: (results?.summary?.scope2_market_based || 0) / 1000,
        scope3_total: (results?.summary?.scope3_emissions || 0) / 1000,
        total_emissions: results?.summary?.total_emissions_tons_co2e || 0,
        
        // Also in ghg_emissions object
        ghg_emissions: {
          lei: "529900HNOAA1KXQJUQ27",
          organization: companyName || "Your Company",
          primary_nace_code: "J.62",
          reporting_period: reportingPeriod,
          scope1: (results?.summary?.scope1_emissions || 0) / 1000,
          scope2_location: (results?.summary?.scope2_location_based || 0) / 1000,
          scope2_market: (results?.summary?.scope2_market_based || 0) / 1000,
          scope3_total: (results?.summary?.scope3_emissions || 0) / 1000,
          total_emissions: results?.summary?.total_emissions_tons_co2e || 0,
          ghg_breakdown: results?.ghg_breakdown || {},
          scope3_breakdown: results?.scope3_breakdown || {}
        },
        
        primary_nace_code: "J.62",
        consolidation_scope: "parent_and_subsidiaries",
        ghg_breakdown: results?.enhancedBreakdown || [],
        esrs_e1_data: {
          reporting_year: parseInt(reportingPeriod) || new Date().getFullYear(),
          base_year: 2020,
          target_year: 2030,
          science_based_targets: true,
          net_zero_commitment: true,
          transition_plan_adopted: true
        }
      };`;

// Replace the entire exportData definition
const start = content.indexOf('const exportData = {');
const end = content.indexOf('};', start) + 2;
content = content.substring(0, start) + newExportData + content.substring(end);

fs.writeFileSync(file, content);
console.log('✅ Added emissions at both top level and ghg_emissions object');
