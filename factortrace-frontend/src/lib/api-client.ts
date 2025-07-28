// factortrace-frontend/src/lib/api-client.ts
import { EmissionData, EvidenceUploadResponse, QualityScores } from '../types/emissions';

class APIClient {
  private baseURL: string;
  private retryCount: number = 3;
  private retryDelay: number = 1000;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  private async fetchWithRetry<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let i = 0; i < this.retryCount; i++) {
      try {
        const response = await fetch(`${this.baseURL}${url}`, {
          ...options,
          headers: {
            ...options.headers,
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
      } catch (error) {
        lastError = error as Error;
        if (i < this.retryCount - 1) {
          await new Promise(resolve => setTimeout(resolve, this.retryDelay * (i + 1)));
        }
      }
    }

    throw lastError || new Error('Unknown error occurred');
  }

  async getEmissions(): Promise<EmissionData[]> {
    return this.fetchWithRetry<EmissionData[]>('/api/v1/emissions');
  }

  async uploadEvidence(
    file: File,
    emissionId: number,
    evidenceType: string,
    description?: string
  ): Promise<EvidenceUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('emission_id', emissionId.toString());
    formData.append('evidence_type', evidenceType);
    if (description) {
      formData.append('description', description);
    }

    return this.fetchWithRetry<EvidenceUploadResponse>(
      '/api/v1/emissions/upload-evidence',
      {
        method: 'POST',
        body: formData,
      }
    );
  }

  async getQualityScore(emissionId: number): Promise<QualityScores> {
    return this.fetchWithRetry<QualityScores>(
      `/api/v1/emissions/data-quality/${emissionId}`
    );
  }

  async deleteEvidence(evidenceId: number): Promise<void> {
    await this.fetchWithRetry<void>(
      `/api/v1/emissions/evidence/${evidenceId}`,
      {
        method: 'DELETE',
      }
    );
  }

  async deleteEmission(emissionId: number): Promise<void> {
    await this.fetchWithRetry<void>(
      `/api/v1/emissions/${emissionId}`,
      {
        method: 'DELETE',
      }
    );
  }
}

export const apiClient = new APIClient();