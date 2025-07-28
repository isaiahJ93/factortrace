// frontend/src/services/emissionsApi.ts

export interface Scope3CalculationRequest {
  category: string;
  activityData: {
    factorName: string;
    quantity: number;
    unit: string;
    calculationMethod: 'activity_based' | 'spend_based';
    region?: string;
  }[];
  reportingPeriod: string;
}

export interface Scope3CalculationResponse {
  success: boolean;
  emissionId: string;
  emissionsTco2e: number;
  uncertaintyPercent: number;
  confidenceInterval: {
    lower: number;
    upper: number;
  };
  dataQualityScore: number;
  calculationHash: string;
}

export const calculateScope3Emissions = async (
  request: Scope3CalculationRequest
): Promise<Scope3CalculationResponse> => {
  const response = await apiClient.post('/emissions/scope3/calculate', request);
  return response.data;
};