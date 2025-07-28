// factortrace-frontend/types/emissions.ts
export interface EmissionData {
  id: number;
  date: string;
  emission_factor_id: number;
  activity_data: number;
  emission_amount?: number;
  co2e_total?: number;
  scope?: number;
  category?: string;
  activity_type?: string;
  activity_unit?: string;
  evidence_type?: string;
  document_url?: string;
  quality_score?: number;
  description?: string;
  location?: string;
  created_at?: string;
  updated_at?: string;
}

export interface QualityScores {
  total_score: number;
  accuracy_score: number;
  completeness_score: number;
  timeliness_score: number;
  consistency_score: number;
  evidence_type: string;
}

export interface EvidenceUploadResponse {
  message: string;
  emission_id: number;
  evidence_document_id: number;
  filename: string;
  evidence_type: string;
  quality_scores: QualityScores;
  document_url: string;
}

export interface QualitySuggestion {
  category: string;
  impact: 'high' | 'medium' | 'low';
  suggestion: string;
  potential_improvement: number;
}