// Emissions API Service - Cache-busted version
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const emissionsAPI = {
  async calculate(emissionsData: any[]) {
    const response = await fetch(`${API_BASE}/api/v1/ghg-calculator/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reporting_period: new Date().getFullYear().toString(),
        emissions_data: emissionsData
      })
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
};
