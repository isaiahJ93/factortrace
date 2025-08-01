// Temporary fix to use the working compliance export endpoint
// In EliteGHGCalculator.tsx, update the exportAsIXBRL function

const exportAsIXBRL = async () => {
  showToast('Generating iXBRL file...', 'info');
  
  try {
    const exportData = {
      format: 'ixbrl',
      data: {
        entity_name: companyName,
        reporting_period: reportingPeriod,
        emissions: {
          scope1: results?.summary?.scope1_emissions || 0,
          scope2: results?.summary?.scope2_location_based || 0,
          scope3: results?.summary?.scope3_emissions || 0
        }
      }
    };
    
    const response = await fetch(`${API_URL}/api/v1/compliance/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(exportData)
    });
    
    if (!response.ok) {
      throw new Error('Export failed');
    }
    
    const result = await response.json();
    
    // Create download
    const blob = new Blob([result.content], { type: 'application/xhtml+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = result.filename || 'emissions_report_ixbrl.html';
    a.click();
    URL.revokeObjectURL(url);
    
    showToast('✅ iXBRL export successful!', 'success');
  } catch (error) {
    console.error('Export error:', error);
    showToast('❌ Export failed', 'error');
  }
};
