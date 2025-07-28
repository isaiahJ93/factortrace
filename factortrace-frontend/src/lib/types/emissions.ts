// Match your backend models exactly
export enum EmissionScope {
  SCOPE_1 = 1,
  SCOPE_2 = 2,
  SCOPE_3 = 3
}

export enum DataSourceType {
  MEASURED = 'measured',
  CALCULATED = 'calculated',
  ESTIMATED = 'estimated',
  DEFAULT = 'default'
}

export enum Scope3Category {
  PURCHASED_GOODS = 'purchased_goods_services',
  CAPITAL_GOODS = 'capital_goods',
  FUEL_ENERGY = 'fuel_energy_activities',
  UPSTREAM_TRANSPORTATION = 'upstream_transportation',
  WASTE_GENERATED = 'waste_generated',
  BUSINESS_TRAVEL = 'business_travel',
  EMPLOYEE_COMMUTING = 'employee_commuting',
  UPSTREAM_LEASED = 'upstream_leased_assets',
  DOWNSTREAM_TRANSPORTATION = 'downstream_transportation',
  PROCESSING_SOLD_PRODUCTS = 'processing_sold_products',
  USE_OF_SOLD_PRODUCTS = 'use_sold_products',
  END_OF_LIFE = 'end_of_life_treatment',
  DOWNSTREAM_LEASED = 'downstream_leased_assets',
  FRANCHISES = 'franchises',
  INVESTMENTS = 'investments'
}

// Match your EmissionCreate schema
export interface EmissionCreate {
  scope: number;
  category: string;
  activity_data: number;
  unit: string;
  emission_factor?: number;
  data_source?: DataSourceType;
  location?: string;
  description?: string;
  
  // Additional fields from your model
  subcategory?: string;
  emission_factor_source?: string;
  data_quality_score?: number;
  uncertainty_percentage?: number;
  country_code?: string;
  reporting_period_start?: string;
  reporting_period_end?: string;
  tags?: string;
  external_reference?: string;
}

// Match your EmissionResponse schema
export interface EmissionResponse extends EmissionCreate {
  id: number;
  amount: number;
  created_at: string;
  updated_at?: string;
  user_id?: number;
  
  // Verification fields
  is_verified: number;
  verified_by?: string;
  verified_at?: string;
}

export interface EmissionsSummary {
  total_emissions: number;
  scope_1_total: number;
  scope_2_total: number;
  scope_3_total: number;
  by_category: Record<string, number>;
  by_scope: Record<string, number>;
}