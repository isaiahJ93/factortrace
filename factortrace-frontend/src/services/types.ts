// src/services/types.ts
export interface Emission {
  id: string;
  category: string;
  subcategory: string;
  framework: string;
  amount: number;
  unit: string;
  percentage: number;
  evidenceCount: number;
  evidenceRequired: boolean;
}

export interface EvidenceUploadResponse {
  evidenceId: string;
  emissionId: string;
  fileName: string;
  fileSize: number;
  fileUrl: string;
  uploadedAt: string;
  status: 'processing' | 'verified' | 'rejected';
}

export interface APIError extends Error {
  status: number;
  code: string;
  retryable: boolean;
}