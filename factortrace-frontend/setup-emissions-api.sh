#!/bin/bash
echo "Creating Emissions API Client..."

cat > src/lib/api/emissions.ts << 'ENDOFFILE'
// frontend/lib/api/emissions.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Types
export interface ActivityData {
  activity_amount: number;
  activity_unit: string;
  emission_factor_id: string;
  region?: string;
  data_quality?: DataQuality;
}

export interface DataQuality {
  temporal: number;
  geographical: number;
  technological: number;
  completeness: number;
  reliability: number;
}

export interface CalculationOptions {
  uncertainty_method?: 'monte_carlo' | 'analytical';
  confidence_level?: number;
  include_uncertainty?: boolean;
}

export interface EmissionResult {
  calculation_id: string;
  emissions_tco2e: number;
  uncertainty_percent: number;
  confidence_interval: {
    lower: number;
    upper: number;
    confidence_level: number;
  };
  percentiles?: {
    p5: number;
    p25: number;
    p75: number;
    p95: number;
  };
  data_quality: {
    overall_score: number;
    dimensions: DataQuality;
  };
  ghg_breakdown: Array<{
    gas_type: string;
    amount: number;
    unit: string;
    gwp_factor: number;
  }>;
  calculation_method?: string;
  tier_level?: string;
  warnings?: string[];
}

export interface EmissionFactor {
  id: number;
  name: string;
  category: string;
  scope: number;
  factor: number;
  unit: string;
  source: string;
  uncertainty_percentage?: number;
  region?: string;
}

export interface Scope3Category {
  id: string;
  display_name: string;
  ghg_protocol_id: string;
  description: string;
  material_sectors: string[];
  calculation_guidance: string;
}

export interface MaterialityAssessment {
  category: string;
  category_name: string;
  is_material: boolean;
  emissions_tco2e?: number;
  percentage_of_total?: number;
  threshold_percentage: number;
  reasons: string[];
  recommendations: string[];
  data_availability: string;
  calculation_feasibility: string;
}

// API Client Class
export class EmissionsAPI {
  private async fetchAPI(endpoint: string, options?: RequestInit) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  }

  // Simple calculation
  async calculateSimple(
    activityValue: number,
    emissionFactor: number,
    unit: string = 'kgCO2e',
    uncertaintyPercent: number = 10
  ) {
    return this.fetchAPI('/emissions/calculate/simple', {
      method: 'POST',
      body: JSON.stringify({
        activity_value: activityValue,
        emission_factor: emissionFactor,
        unit,
        uncertainty_percent: uncertaintyPercent,
      }),
    });
  }

  // Advanced calculation with uncertainty
  async calculateAdvanced(
    activityData: ActivityData[],
    options: CalculationOptions = {}
  ): Promise<EmissionResult> {
    return this.fetchAPI('/emissions/calculate/advanced', {
      method: 'POST',
      body: JSON.stringify({
        activity_data: activityData,
        calculation_options: {
          uncertainty_method: 'monte_carlo',
          confidence_level: 95,
          ...options,
        },
      }),
    });
  }

  // Calculate Scope 3 category
  async calculateScope3(
    category: string,
    activityData: Record<string, { amount: number; unit: string; region?: string }>,
    method: 'activity_based' | 'spend_based' = 'activity_based'
  ) {
    return this.fetchAPI(`/emissions/calculate/scope3/${category}?method=${method}`, {
      method: 'POST',
      body: JSON.stringify(activityData),
    });
  }

  // Search emission factors
  async searchFactors(params: {
    query?: string;
    scope?: number;
    category?: string;
    region?: string;
    limit?: number;
  }): Promise<{ total: number; factors: EmissionFactor[] }> {
    const queryString = new URLSearchParams(
      Object.entries(params)
        .filter(([_, v]) => v !== undefined)
        .map(([k, v]) => [k, String(v)])
    ).toString();

    return this.fetchAPI(`/emissions/factors/search?${queryString}`);
  }

  // Get Scope 3 categories
  async getScope3Categories(): Promise<Record<string, Scope3Category>> {
    return this.fetchAPI('/emissions/scope3/categories');
  }

  // Assess materiality
  async assessMateriality(
    sector: string,
    annualRevenue?: number,
    currentEmissions?: Record<string, number>
  ): Promise<{
    sector: string;
    assessments: MaterialityAssessment[];
  }> {
    return this.fetchAPI('/emissions/materiality/assess', {
      method: 'POST',
      body: JSON.stringify({
        sector,
        annual_revenue: annualRevenue,
        current_emissions: currentEmissions,
      }),
    });
  }

  // Generate compliance report
  async generateComplianceReport(
    standard: 'ESRS' | 'CDP' | 'TCFD' | 'SBTi',
    emissionsByCategory: Record<string, number>,
    reportingPeriod?: string
  ) {
    const params = new URLSearchParams({ standard });
    if (reportingPeriod) params.append('reporting_period', reportingPeriod);

    return this.fetchAPI(`/emissions/reports/compliance?${params}`, {
      method: 'POST',
      body: JSON.stringify(emissionsByCategory),
    });
  }

  // Get emissions summary
  async getEmissionsSummary() {
    return this.fetchAPI('/emissions/summary');
  }

  // Create emission record
  async createEmission(data: any) {
    return this.fetchAPI('/emissions/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Export as CSV
  async exportCSV(params?: { scope?: number; startDate?: string; endDate?: string }) {
    const queryString = new URLSearchParams(
      Object.entries(params || {})
        .filter(([_, v]) => v !== undefined)
        .map(([k, v]) => [k, String(v)])
    ).toString();

    const response = await fetch(`${API_BASE_URL}/emissions/export/csv?${queryString}`);
    if (!response.ok) throw new Error('Export failed');
    
    return response.blob();
  }
}

// Export singleton instance
export const emissionsAPI = new EmissionsAPI();
ENDOFFILE

echo "✅ Emissions API Client created!"
