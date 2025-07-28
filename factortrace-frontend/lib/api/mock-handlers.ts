// lib/api/mock-handlers.ts
// Clean mock handlers for development

export const mockHandlers = {
  '/api/vouchers/validate': async (data: any) => {
    return {
      valid: true,
      warnings: [],
      suggestions: ['Looking good!']
    };
  },
  
  '/api/vouchers/drafts': async (data: any) => {
    return {
      id: `draft-${Date.now()}`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      data
    };
  },
  
  '/api/reports/generate-elite': async (data: any) => {
    return {
      success: true,
      reportId: `report-${Date.now()}`,
      url: '/api/reports/mock-report.pdf'
    };
  },
  
  '/api/vouchers/suggestions/manufacturing': async () => {
    return {
      suggestions: [
        'Consider renewable energy certificates',
        'Implement ISO 14001 standards',
        'Track Scope 3 emissions from suppliers'
      ]
    };
  }
};

// Type definitions
interface VoucherData {
  [key: string]: any;
}

interface ValidationResult {
  valid: boolean;
  warnings: string[];
  suggestions: string[];
}

// Mock API client
export class MockAPIClient {
  async validate(data: VoucherData): Promise<ValidationResult> {
    return mockHandlers['/api/vouchers/validate'](data);
  }
  
  async saveDraft(data: VoucherData) {
    return mockHandlers['/api/vouchers/drafts'](data);
  }
  
  async generateReport(data: VoucherData) {
    return mockHandlers['/api/reports/generate-elite'](data);
  }
}

// Export a singleton instance
export const mockAPI = new MockAPIClient();