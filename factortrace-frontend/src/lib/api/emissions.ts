/**
 * GHG Emissions Calculator API Client
 * Type-safe integration with your FastAPI backend
 */

// Types matching your backend models
export interface EmissionInput {
  activity_type: string;
  amount: number;
  unit: string;
}

export interface CalculateEmissionsRequest {
  company_id?: string;
  reporting_period: string;
  emissions_data: EmissionInput[];
}

export interface EmissionBreakdown {
  activity_type: string;
  scope: string;
  emissions_kg_co2e: number;
  unit: string;
  calculation_method: string;
}

export interface CalculateEmissionsResponse {
  total_emissions_kg_co2e: number;
  total_emissions_tons_co2e: number;
  scope1_emissions: number;
  scope2_emissions: number;
  scope3_emissions: number;
  breakdown: EmissionBreakdown[];
  reporting_period: string;
  calculation_date: string;
}

export interface EmissionFactor {
  activity_type: string;
  display_name: string;
  unit: string;
  scope: string;
  factor: number;
  factor_unit: string;
}

export interface ActivityType {
  value: string;
  label: string;
  unit: string;
}

// API client class
export class EmissionsAPI {
  private baseURL: string;

  constructor(baseURL: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1') {
    this.baseURL = baseURL;
  }

  async calculateEmissions(request: CalculateEmissionsRequest): Promise<CalculateEmissionsResponse> {
    const response = await fetch(`${this.baseURL}/ghg-calculator/calculate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to calculate emissions');
    }

    return response.json();
  }

  async getEmissionFactors(): Promise<{ emission_factors: EmissionFactor[] }> {
    const response = await fetch(`${this.baseURL}/ghg-calculator/emission-factors`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch emission factors');
    }

    return response.json();
  }

  async getActivityTypes(): Promise<Record<string, ActivityType[]>> {
    const response = await fetch(`${this.baseURL}/ghg-calculator/activity-types`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch activity types');
    }

    return response.json();
  }
}