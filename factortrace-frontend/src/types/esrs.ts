// src/types/esrs.ts
// Complete type definitions for ESRS E1 Climate Change reporting

export interface ESRSEntity {
  name: string;
  lei: string; // Legal Entity Identifier (20 characters)
  identifier_scheme: string;
  sector: string;
  primary_nace_code: string; // Format: "XX.XX"
  secondary_nace_codes?: string[];
  consolidation_scope: 'consolidated' | 'parent' | 'individual';
  reporting_boundary: 'financial_control' | 'operational_control' | 'equity_share';
}

export interface ESRSPeriod {
  start_date: string; // ISO date
  end_date: string; // ISO date
  reporting_year: number;
  comparative_year: number;
}

export interface ESRSTransitionPlan {
  has_transition_plan: boolean;
  aligned_1_5c: boolean;
  net_zero_target_year: number;
  science_based_targets: boolean;
  interim_targets?: Array<{
    year: number;
    reduction_percent: number;
  }>;
}

export interface ESRSTarget {
  base_year: number;
  target_year: number;
  target_reduction_percent: number;
  scopes_covered: ('scope1' | 'scope2' | 'scope3')[];
  target_type?: 'absolute' | 'intensity';
}

export interface ESRSScope3Categories {
  cat1_purchased_goods: number;
  cat2_capital_goods: number;
  cat3_fuel_energy: number;
  cat4_upstream_transport: number;
  cat5_waste: number;
  cat6_business_travel: number;
  cat7_employee_commuting: number;
  cat8_upstream_leased: number;
  cat9_downstream_transport: number;
  cat10_processing_sold: number;
  cat11_use_of_sold: number;
  cat12_end_of_life: number;
  cat13_downstream_leased: number;
  cat14_franchises: number;
  cat15_investments: number;
}

export interface ESRSGHGBreakdown {
  co2_fossil: number;
  co2_biogenic: number;
  ch4: number;
  n2o: number;
  hfcs: number;
  pfcs: number;
  sf6: number;
  nf3: number;
}

export interface ESRSGHGEmissions {
  scope1_total: number;
  scope1_breakdown?: {
    stationary_combustion: number;
    mobile_combustion: number;
    process_emissions: number;
    fugitive_emissions: number;
  };
  scope2_location: number;
  scope2_market: number;
  scope3_total: number;
  scope3_categories: ESRSScope3Categories;
  total_ghg_emissions: number;
  ghg_breakdown: ESRSGHGBreakdown;
  intensity_metrics: {
    per_revenue: number;
    per_employee: number;
    per_unit_produced?: number | null;
  };
}

export interface ESRSClimateChange {
  transition_plan: ESRSTransitionPlan;
  targets: {
    absolute_targets: ESRSTarget[];
    intensity_targets: ESRSTarget[];
  };
  ghg_emissions: ESRSGHGEmissions;
  carbon_removals: {
    total_removals: number;
    removal_projects: Array<{
      project_name: string;
      removal_amount: number;
      methodology: string;
    }>;
  };
  carbon_pricing: {
    exposed_to_ets: boolean;
    total_emissions_under_ets: number;
    carbon_credits_purchased: number;
  };
}

export interface ESRSDataQuality {
  estimation_methods_used: boolean;
  third_party_verified: boolean;
  verification_standard?: string | null;
  data_gaps_disclosed: boolean;
  calculation_methodology?: string;
}

export interface ESRSMetadata {
  report_type: string;
  taxonomy_version: string;
  creation_timestamp: string;
  preparer_name: string;
  preparer_email: string;
  language: string;
  currency: string;
}

export interface ESRSExportData {
  entity: ESRSEntity;
  period: ESRSPeriod;
  climate_change: ESRSClimateChange;
  data_quality: ESRSDataQuality;
  metadata: ESRSMetadata;
}

// Company info extension for ESRS compliance
export interface ESRSCompanyInfo {
  companyName: string;
  lei?: string;
  sector?: string;
  primary_nace_code?: string;
  secondary_nace_codes?: string[];
  reportingPeriod: string;
  revenue?: number;
  employees?: number;
  hasTransitionPlan?: boolean;
  aligned_1_5c?: boolean;
  netZeroTargetYear?: number;
  scienceBasedTargets?: boolean;
  preparerName?: string;
  preparerEmail?: string;
}

// Validation utilities
export const ESRSValidation = {
  isValidLEI: (lei: string): boolean => {
    return /^[A-Z0-9]{20}$/.test(lei);
  },
  
  isValidNACE: (code: string): boolean => {
    return /^\d{2}\.\d{2}$/.test(code);
  },
  
  validateGHGData: (emissions: Partial<ESRSGHGEmissions>): string[] => {
    const errors: string[] = [];
    
    if (!emissions.scope1_total || emissions.scope1_total < 0) {
      errors.push('Scope 1 emissions must be a positive number');
    }
    
    if (!emissions.scope2_location || emissions.scope2_location < 0) {
      errors.push('Scope 2 location-based emissions must be a positive number');
    }
    
    if (emissions.scope3_total && emissions.scope3_categories) {
      const categoriesSum = Object.values(emissions.scope3_categories).reduce((a, b) => a + b, 0);
      if (Math.abs(categoriesSum - emissions.scope3_total) > 0.01) {
        errors.push('Scope 3 categories must sum to total Scope 3 emissions');
      }
    }
    
    return errors;
  },
};