const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

class APIClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    console.log('API Request:', url);
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      console.error('API Error:', response.status, response.statusText);
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Update these to use /api/v1 prefix
  async getEmissions() {
    return this.request<any[]>('/api/v1/emissions');
  }

  async getEmissionsSummary() {
    return this.request<any>('/api/v1/emissions/summary');
  }

  async createVoucher(data: any) {
    return this.request('/api/v1/vouchers', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const api = new APIClient();
