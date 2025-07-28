// Core interfaces for frontend
export interface EmissionFactor {
  value: number;
  unit: string;
  source: string;
  uncertainty: number;
  lastUpdated: string;
  validUntil?: string;
  regions?: Record<string, number>;
  lifecycle_stage?: string;
  methodology?: string;
  dataQuality?: DataQualityIndicators;
}

export interface DataQualityIndicators {
  temporal: number; // 1-5 scale
  geographical: number;
  technological: number;
  completeness: number;
  reliability: number;
}

export interface CategoryMetadata {
  description: string;
  calculation_methods: string[];
  data_quality_indicators: DataQualityIndicators;
  material_sectors?: string[];
  esrs_mapping?: string[];
  cdp_questions?: string[];
  sbti_guidance?: string;
}

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

export interface Evidence {
  evidenceId: string;
  fileName: string;
  fileSize: number;
  evidenceType: 'Photo' | 'Invoice' | 'Certificate' | 'Report' | 'Other';
  uploadedAt: string;
  uploadedBy: {
    userId: string;
    name: string;
  };
  status: 'processing' | 'verified' | 'rejected';
  thumbnailUrl?: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}