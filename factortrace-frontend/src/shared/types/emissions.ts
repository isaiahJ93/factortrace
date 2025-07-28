export interface Emission {
  id: string;
  scope: number;
  category: string;
  activity_data: number;
  unit: string;
  emission_factor?: number;
  amount: number;
  created_at: string;
  updated_at: string;
}

export interface EmissionsSummary {
  scope1_total: number;
  scope2_total: number;
  scope3_total: number;
  total_emissions: number;
}
