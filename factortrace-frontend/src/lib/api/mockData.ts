export const mockVoucherData = {
  companyName: 'Demo Company Ltd',
  lei: 'DEMO123456789012345',
  reportingPeriod: 'Q1',
  reportingYear: '2024',
  standard: 'CSRD',
  
  scope1: { value: '234.5', uncertainty: 5, quality: 85 },
  scope2: { value: '156.2', uncertainty: 10, quality: 80 },
  scope3: { value: '856.6', uncertainty: 15, quality: 75 },
  
  primaryDataPercentage: 65,
  estimatesPercentage: 25,
  proxiesPercentage: 10,
  verificationLevel: 'limited',
  
  notes: 'Q1 2024 emissions data - verified by internal audit team',
  attachments: []
};