#!/usr/bin/env python3
import re

with open('src/components/emissions/EliteGHGCalculator.tsx', 'r') as f:
    content = f.read()

# Update the exportAsIXBRL function to match ESRS requirements
new_export_function = '''const exportAsIXBRL = async () => {
    showToast('Generating iXBRL file...', 'info');
    
    try {
      // Prepare data for ESRS E1 endpoint
      const exportData = {
        organization: companyName || 'Test Organization',
        lei: "529900HNOAA1KXQJUQ27", // You should get this from company settings
        reporting_period: parseInt(reportingPeriod) || new Date().getFullYear(),
        force_generation: true,
        
        // Emissions data in tons
        total_emissions: (results?.totalEmissions?.total || 0) / 1000,
        scope1: (results?.totalEmissions?.scope1 || 0) / 1000,
        scope2_location: (results?.totalEmissions?.scope2 || 0) / 1000,
        scope2_market: (results?.totalEmissions?.scope2 || 0) / 1000, // Same as location for now
        scope3_total: (results?.totalEmissions?.scope3 || 0) / 1000,
        
        // Additional ESRS data
        primary_nace_code: "J.62", // Default to IT services
        consolidation_scope: "parent_and_subsidiaries",
        
        // Include breakdown if available
        ghg_breakdown: results?.enhancedBreakdown || [],
        esrs_e1_data: {
          reporting_year: parseInt(reportingPeriod) || new Date().getFullYear(),
          base_year: 2020,
          target_year: 2030,
          science_based_targets: true,
          net_zero_commitment: true,
          transition_plan_adopted: true
        }
      };
      
      console.log('Sending export data:', exportData);
      
      const response = await fetch(`${API_URL}/api/v1/esrs-e1/export-ixbrl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(exportData)
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Export error response:', errorText);
        throw new Error(errorText || 'Export failed');
      }
      
      const result = await response.json();
      console.log('Export result:', result);
      
      // Handle the response - could be different formats
      let content = result.xhtml_content || result.content || result;
      if (typeof content === 'object') {
        content = JSON.stringify(content);
      }
      
      // Create download
      const blob = new Blob([content], { type: 'application/xhtml+xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename || `ESRS_E1_Report_${companyName}_${reportingPeriod}.xhtml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showToast('✅ ESRS E1 iXBRL export successful!', 'success');
      
    } catch (error: any) {
      console.error('Export error:', error);
      showToast(`❌ Export failed: ${error.message}`, 'error');
    }
  };'''

# Replace the entire exportAsIXBRL function
pattern = r'const exportAsIXBRL = async \(\) => \{[\s\S]*?\n  \};'
content = re.sub(pattern, new_export_function, content, count=1)

with open('src/components/emissions/EliteGHGCalculator.tsx', 'w') as f:
    f.write(content)

print("✅ Updated frontend to use ESRS endpoint with proper data structure")
