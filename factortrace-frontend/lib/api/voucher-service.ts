// lib/api/voucher-service.ts

interface VoucherData {
  company_name: string;
  lei: string;
  reporting_period: string;
  reporting_year: string;
  standard: string;
  scope1: {
    value: number;
    uncertainty: number;
    quality: number;
    methodology: string;
  };
  scope2: {
    value: number;
    uncertainty: number;
    quality: number;
    methodology: string;
  };
  scope3: {
    value: number;
    uncertainty: number;
    quality: number;
    methodology: string;
  };
  primary_data_percentage: number;
  estimates_percentage: number;
  proxies_percentage: number;
  verification_level: string;
  data_collection_method: string;
  notes: string;
  targets: {
    reduction: number;
    baseYear: string;
    targetYear: string;
  };
}

interface ValidationResult {
  valid: boolean;
  warnings: string[];
  suggestions: string[];
  errors?: string[];
}

interface DraftResult {
  id: string;
  created_at: string;
  updated_at: string;
}

interface GenerateResult {
  report_id: string;
  download_url: string;
  status: string;
  created_at: string;
}

interface SuggestionResult {
  industry: string;
  suggestions: {
    scope1: { typical: number; range: { min: number; max: number } };
    scope2: { typical: number; range: { min: number; max: number } };
    scope3: { typical: number; range: { min: number; max: number } };
  };
}

// Mock handlers for development
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === 'true';

const mockHandlers = {
  validate: async (data: VoucherData): Promise<ValidationResult> => {
    await new Promise(resolve => setTimeout(resolve, 500));

    const warnings = [];
    const suggestions = [];

    if (data.scope3.value > data.scope1.value + data.scope2.value) {
      suggestions.push('Scope 3 emissions are typically the largest portion. Consider more detailed supplier engagement.');
    }

    if (data.primary_data_percentage < 50) {
      warnings.push('Primary data percentage is below 50%. Consider improving data collection methods.');
    }

    if (data.verification_level === 'none') {
      warnings.push('No third-party verification selected. Consider at least limited assurance for credibility.');
    }

    return { valid: true, warnings, suggestions };
  },

  saveDraft: async (data: VoucherData): Promise<DraftResult> => {
    await new Promise(resolve => setTimeout(resolve, 300));
    return {
      id: `draft-${Date.now()}`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  },

  generateXBRL: async (data: any): Promise<GenerateResult> => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    return {
      report_id: `xbrl-${Date.now()}`,
      download_url: `/api/reports/download/xbrl-${Date.now()}.xml`,
      status: 'completed',
      created_at: new Date().toISOString(),
    };
  },

  getSuggestions: async (): Promise<SuggestionResult> => {
    await new Promise(resolve => setTimeout(resolve, 400));
    return {
      industry: 'manufacturing',
      suggestions: {
        scope1: { typical: 250, range: { min: 150, max: 350 } },
        scope2: { typical: 180, range: { min: 100, max: 260 } },
        scope3: { typical: 820, range: { min: 600, max: 1040 } },
      },
    };
  },
};

class VoucherService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  async validate(data: VoucherData): Promise<ValidationResult> {
    if (USE_MOCKS) {
      return mockHandlers.validate(data);
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/vouchers/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) throw new Error('Validation failed');
      return await response.json();
    } catch (error) {
      console.error('Validation error:', error);
      return {
        valid: false,
        warnings: [],
        suggestions: [],
        errors: ['Failed to validate data. Please try again.'],
      };
    }
  }

  async saveDraft(data: VoucherData): Promise<DraftResult> {
    if (USE_MOCKS) {
      return mockHandlers.saveDraft(data);
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/vouchers/drafts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) throw new Error('Failed to save draft');
      return await response.json();
    } catch (error) {
      console.error('Save draft error:', error);
      throw error;
    }
  }

  async generateXBRL(data: VoucherData): Promise<GenerateResult> {
    if (USE_MOCKS) {
      return mockHandlers.generateXBRL(data);
    }

    try {
      const apiPayload = {
        report_type: 'emissions',
        format: 'ixbrl',
        facts: [
          {
            concept: 'TotalEmissions',
            value: (data.scope1.value + data.scope2.value + data.scope3.value).toString(),
            unit: 'tCO2e',
            period: `${data.reporting_year}-${data.reporting_period}`,
          },
          {
            concept: 'Scope1Emissions',
            value: data.scope1.value.toString(),
            unit: 'tCO2e',
            period: `${data.reporting_year}-${data.reporting_period}`,
          },
          {
            concept: 'Scope2Emissions',
            value: data.scope2.value.toString(),
            unit: 'tCO2e',
            period: `${data.reporting_year}-${data.reporting_period}`,
          },
          {
            concept: 'Scope3Emissions',
            value: data.scope3.value.toString(),
            unit: 'tCO2e',
            period: `${data.reporting_year}-${data.reporting_period}`,
          },
        ],
        metadata: {
          entity_name: data.company_name,
          entity_identifier: data.lei,
          reporting_period: data.reporting_period,
          reporting_year: data.reporting_year,
          standard: data.standard,
          data_quality_score: this.calculateOverallQuality(data),
          verification_level: data.verification_level,
          primary_data_percentage: data.primary_data_percentage,
          data_collection_method: data.data_collection_method,
        },
        period: {
          start_date: this.getPeriodStartDate(data.reporting_year, data.reporting_period),
          end_date: this.getPeriodEndDate(data.reporting_year, data.reporting_period),
        },
      };

      const response = await fetch(`${this.baseUrl}/api/reports/generate-elite`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(apiPayload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate XBRL');
      }

      return await response.json();
    } catch (error) {
      console.error('Generate XBRL error:', error);
      throw error;
    }
  }

  async getSuggestions(industry: string): Promise<SuggestionResult> {
    if (USE_MOCKS) {
      return mockHandlers.getSuggestions();
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/vouchers/suggestions/${industry}`);
      if (!response.ok) throw new Error('Failed to fetch suggestions');
      return await response.json();
    } catch (error) {
      console.error('Get suggestions error:', error);
      return mockHandlers.getSuggestions(); // Fallback to mock data
    }
  }

  async loadDraft(draftId: string): Promise<VoucherData> {
    try {
      const response = await fetch(`${this.baseUrl}/api/vouchers/drafts/${draftId}`);
      if (!response.ok) throw new Error('Failed to load draft');
      return await response.json();
    } catch (error) {
      console.error('Load draft error:', error);
      throw error;
    }
  }

  async listDrafts(): Promise<DraftResult[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/vouchers/drafts`);
      if (!response.ok) throw new Error('Failed to list drafts');
      return await response.json();
    } catch (error) {
      console.error('List drafts error:', error);
      return [];
    }
  }

  private calculateOverallQuality(data: VoucherData): number {
    const weights = { scope1: 0.2, scope2: 0.2, scope3: 0.6 };
    const quality =
      data.scope1.quality * weights.scope1 +
      data.scope2.quality * weights.scope2 +
      data.scope3.quality * weights.scope3;
    return Math.round(quality);
  }

  private getPeriodStartDate(year: string, period: string): string {
    switch (period) {
      case 'Q1': return `${year}-01-01`;
      case 'Q2': return `${year}-04-01`;
      case 'Q3': return `${year}-07-01`;
      case 'Q4': return `${year}-10-01`;
      case 'FY': return `${year}-01-01`;
      default: return `${year}-01-01`;
    }
  }

  private getPeriodEndDate(year: string, period: string): string {
    switch (period) {
      case 'Q1': return `${year}-03-31`;
      case 'Q2': return `${year}-06-30`;
      case 'Q3': return `${year}-09-30`;
      case 'Q4': return `${year}-12-31`;
      case 'FY': return `${year}-12-31`;
      default: return `${year}-12-31`;
    }
  }
}

// Export singleton instance
export const voucherService = new VoucherService();