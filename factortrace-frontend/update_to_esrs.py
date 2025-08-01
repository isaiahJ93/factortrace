#!/usr/bin/env python3
import re

with open('src/components/emissions/EliteGHGCalculator.tsx', 'r') as f:
    content = f.read()

# Update the export data structure for ESRS
old_pattern = r'const exportData = \{[^}]+\};'
new_data = '''const exportData = {
        organization: companyName,
        lei: "529900HNOAA1KXQJUQ27",  // Add a valid LEI
        reporting_period: new Date(reportingPeriod).getFullYear(),
        force_generation: true,
        total_emissions: results?.summary?.total_emissions_tons_co2e || 0,
        scope1: (results?.summary?.scope1_emissions || 0) / 1000,
        scope2_location: (results?.summary?.scope2_location_based || 0) / 1000,
        scope2_market: (results?.summary?.scope2_market_based || 0) / 1000,
        scope3_total: (results?.summary?.scope3_emissions || 0) / 1000,
        primary_nace_code: "J.62"  // Default NACE code
      };'''

# Find in exportAsIXBRL function
pattern = r'const exportData = \{[^}]+format: \'ixbrl\'[^}]+\};'
content = re.sub(pattern, new_data, content, flags=re.DOTALL)

with open('src/components/emissions/EliteGHGCalculator.tsx', 'w') as f:
    f.write(content)

print("✅ Updated to use ESRS data structure")
