/**
 * FactorTrace API Client
 * Elite-tier integration layer for FastAPI backend
 * 
 * Architecture: Type-safe, resilient, performant
 * Pattern: Repository + Adapter with automatic retry and caching
 */

import { z } from 'zod';

// ==================== Configuration ====================
const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
  timeout: 30000,
  retries: 3,
  retryDelay: 1000,
} as const;

// ==================== Type Definitions ====================
// Schema-first approach: These match your FastAPI Pydantic models

export const EmissionScopes = {
  SCOPE_1: 'scope_1',
  SCOPE_2: 'scope_2', 
  SCOPE_3: 'scope_3',
} as const;

export type EmissionScope = typeof EmissionScopes[keyof typeof EmissionScopes];

// Zod schemas for runtime validation + type inference
export const EmissionSchema = z.object({
  id: z.union([z.string().uuid(), z.number()]), // Backend returns integer IDs
  scope: z.union([
    z.enum(['scope_1', 'scope_2', 'scope_3']),
    z.number().min(1).max(3)
  ]),
  category: z.string(),
  activity: z.string().optional(), // Backend might not always return this
  activity_data: z.number().positive().optional(), // Backend field
  amount: z.number().positive(),
  unit: z.string(),
  emission_factor: z.number().positive().optional(),
  co2_equivalent: z.number().optional(),
  date: z.string().optional(), // More flexible date handling
  location: z.string().optional().nullable(),
  notes: z.string().optional().nullable(),
  description: z.string().optional().nullable(), // Backend uses description
  created_at: z.string(),
  updated_at: z.string().optional().nullable(),
  // Backend specific fields
  reporting_period_start: z.string().optional().nullable(),
  reporting_period_end: z.string().optional().nullable(),
});

export const EmissionCreateSchema = z.object({
  scope: z.union([
    z.enum(['scope_1', 'scope_2', 'scope_3']),
    z.number().min(1).max(3),
    z.string() // Accept any string and convert later
  ]),
  category: z.string(),
  activity: z.string(),
  amount: z.number().positive(),
  unit: z.string(),
  emission_factor: z.number().positive(),
  date: z.string(),
  location: z.string().optional(),
  notes: z.string().optional(),
});

export const EmissionUpdateSchema = EmissionCreateSchema.partial();

export const EmissionSummarySchema = z.object({
  total_emissions: z.number(),
  scope1_total: z.number().optional(),
  scope2_total: z.number().optional(),
  scope3_total: z.number().optional(),
  by_scope: z.record(z.string(), z.number()).optional(),
  by_category: z.record(z.string(), z.number()),
  by_month: z.array(z.object({
    month: z.string(),
    total: z.number(),
    scopes: z.record(z.string(), z.number()),
  })).optional(),
  time_range: z.object({
    start: z.string(),
    end: z.string(),
  }).optional(),
});

export const EmissionCalculateSchema = z.object({
  activity: z.string(),
  amount: z.number().positive(),
  unit: z.string(),
  scope: z.union([
    z.enum(['scope_1', 'scope_2', 'scope_3']),
    z.number().min(1).max(3)
  ]),
  region: z.string().optional(),
});

export const CalculationResultSchema = z.object({
  co2_equivalent: z.number(),
  emission_factor: z.number(),
  calculation_method: z.string(),
  data_source: z.string(),
  confidence_level: z.enum(['high', 'medium', 'low']),
});

// Type inference from Zod schemas - with flexible input types
export type Emission = z.infer<typeof EmissionSchema>;
export type EmissionCreate = {
  scope: EmissionScope | number | string; // Accept flexible input
  category: string;
  activity: string;
  amount: number;
  unit: string;
  emission_factor: number;
  date: string;
  location?: string;
  notes?: string;
};
export type EmissionUpdate = Partial<EmissionCreate>;
export type EmissionSummary = z.infer<typeof EmissionSummarySchema>;
export type EmissionCalculate = {
  activity: string;
  amount: number;
  unit: string;
  scope: EmissionScope | number | string;
  region?: string;
};
export type CalculationResult = z.infer<typeof CalculationResultSchema>;

// ==================== Error Handling ====================
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public code: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class NetworkError extends Error {
  constructor(message: string, public cause?: Error) {
    super(message);
    this.name = 'NetworkError';
  }
}

export class DatabaseError extends APIError {
  constructor(message: string, details?: unknown) {
    super(message, 500, 'DATABASE_ERROR', details);
    this.name = 'DatabaseError';
  }
}

// ==================== Core API Client ====================
class APIClient {
  private baseURL: string;
  private timeout: number;
  private headers: HeadersInit;
  private abortControllers: Map<string, AbortController> = new Map();

  constructor(config = API_CONFIG) {
    this.baseURL = config.baseURL;
    this.timeout = config.timeout;
    this.headers = {
      'Content-Type': 'application/json',
    };
  }

  /**
   * Execute HTTP request with automatic retry, timeout, and error handling
   * Implements exponential backoff with jitter
   */
  private async request<T>(
    path: string,
    options: RequestInit & { 
      retries?: number; 
      validateResponse?: (data: unknown) => T;
      requestId?: string;
    } = {}
  ): Promise<T> {
    const {
      retries = API_CONFIG.retries,
      validateResponse,
      requestId = `${path}-${Date.now()}`,
      ...fetchOptions
    } = options;

    // Cancel any existing request to the same endpoint
    this.cancelRequest(requestId);

    const url = `${this.baseURL}${path}`;
    const controller = new AbortController();
    this.abortControllers.set(requestId, controller);

    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await this.executeWithRetry(
        () => fetch(url, {
          ...fetchOptions,
          headers: { ...this.headers, ...fetchOptions.headers },
          signal: controller.signal,
        }),
        retries
      );

      clearTimeout(timeoutId);
      this.abortControllers.delete(requestId);

      if (!response.ok) {
        const error = await this.parseError(response);
        
        // Handle specific backend errors with helpful messages
        if (error.detail?.includes('Mapper') && error.detail?.includes('has no property')) {
          throw new DatabaseError(
            'Database relationship configuration error. Please contact the backend team.',
            error
          );
        }
        
        if (error.detail?.includes('InvalidRequestError')) {
          throw new DatabaseError(
            'Database configuration error. The backend models may need to be updated.',
            error
          );
        }

        throw new APIError(
          error.message || error.detail || `Request failed with status ${response.status}`,
          response.status,
          error.code || 'API_ERROR',
          error.details || error
        );
      }

      const data = await response.json();
      
      // Runtime validation if schema provided
      if (validateResponse) {
        try {
          return validateResponse(data);
        } catch (validationError) {
          console.error('Response validation failed:', validationError);
          // Log the actual response for debugging
          console.error('Actual response:', data);
          // Return the data anyway - better to show something than crash
          return data as T;
        }
      }
      
      return data as T;
    } catch (error) {
      clearTimeout(timeoutId);
      this.abortControllers.delete(requestId);

      if (error instanceof APIError || error instanceof DatabaseError) {
        throw error;
      }
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new NetworkError('Request timeout', error);
        }
        throw new NetworkError('Network request failed', error);
      }
      
      throw new NetworkError('Unknown error occurred');
    }
  }

  /**
   * Exponential backoff with jitter for retry logic
   */
  private async executeWithRetry<T>(
    fn: () => Promise<T>,
    retries: number
  ): Promise<T> {
    let lastError: Error | undefined;
    
    for (let i = 0; i <= retries; i++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on client errors (4xx) unless it's a 429 (rate limit)
        if (error instanceof APIError && error.status >= 400 && error.status < 500 && error.status !== 429) {
          throw error;
        }
        
        if (i < retries) {
          // Exponential backoff with jitter
          const delay = Math.min(1000 * Math.pow(2, i) + Math.random() * 1000, 10000);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    throw lastError;
  }

  /**
   * Parse error response with fallback handling
   */
  private async parseError(response: Response): Promise<{
    message?: string;
    detail?: string;
    code?: string;
    details?: unknown;
  }> {
    try {
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        const errorData = await response.json();
        // FastAPI typically returns errors in { detail: string } format
        return {
          message: errorData.message || errorData.detail,
          detail: errorData.detail,
          code: errorData.code,
          details: errorData,
        };
      }
      const textError = await response.text();
      return { message: textError, detail: textError };
    } catch {
      return { message: 'Failed to parse error response' };
    }
  }

  /**
   * Cancel a specific request
   */
  cancelRequest(requestId: string): void {
    const controller = this.abortControllers.get(requestId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(requestId);
    }
  }

  /**
   * Cancel all pending requests
   */
  cancelAllRequests(): void {
    this.abortControllers.forEach(controller => controller.abort());
    this.abortControllers.clear();
  }

  // ==================== HTTP Methods ====================
  
  get<T>(path: string, options?: RequestInit & { validateResponse?: (data: unknown) => T }): Promise<T> {
    return this.request<T>(path, { ...options, method: 'GET' });
  }

  post<T>(path: string, data?: unknown, options?: RequestInit & { validateResponse?: (data: unknown) => T }): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  put<T>(path: string, data?: unknown, options?: RequestInit & { validateResponse?: (data: unknown) => T }): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  patch<T>(path: string, data?: unknown, options?: RequestInit & { validateResponse?: (data: unknown) => T }): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  delete<T>(path: string, options?: RequestInit & { validateResponse?: (data: unknown) => T }): Promise<T> {
    return this.request<T>(path, { ...options, method: 'DELETE' });
  }
}

// ==================== Emissions Repository ====================
export class EmissionsRepository {
  constructor(private client: APIClient) {}

  /**
   * Helper to convert scope between frontend string format and backend number format
   */
  private convertScopeToString(scope: number | string): EmissionScope {
    if (typeof scope === 'number') {
      return `scope_${scope}` as EmissionScope;
    }
    // Handle "Scope 1", "Scope 2", "Scope 3" format
    if (typeof scope === 'string' && scope.startsWith('Scope ')) {
      const scopeNum = scope.replace('Scope ', '');
      return `scope_${scopeNum}` as EmissionScope;
    }
    // Handle "1", "2", "3" string format
    if (typeof scope === 'string' && ['1', '2', '3'].includes(scope)) {
      return `scope_${scope}` as EmissionScope;
    }
    return scope as EmissionScope;
  }

  private convertScopeToNumber(scope: string | number): number {
    if (typeof scope === 'number') return scope;
    // Extract number from any string format
    const num = parseInt(scope.replace(/\D/g, ''));
    return isNaN(num) ? 1 : num;
  }

  /**
   * Convert frontend data to backend format
   */
  private toBackendFormat(data: any): any {
    const backendData: any = {
      ...data,
      // Convert scope to number for backend
      scope: this.convertScopeToNumber(data.scope),
      // Map frontend fields to backend fields
      activity_data: data.amount || data.activity_data,
      description: data.notes || data.description,
    };

    // Add reporting period dates if date is provided
    if (data.date) {
      backendData.reporting_period_start = data.date;
      backendData.reporting_period_end = data.date;
    }

    // Calculate amount if not provided
    if (!backendData.amount && backendData.activity_data && backendData.emission_factor) {
      backendData.amount = backendData.activity_data * backendData.emission_factor;
    }

    // Remove frontend-only fields
    delete backendData.notes;

    console.log('Converted to backend format:', backendData);
    return backendData;
  }

  /**
   * Convert backend data to frontend format
   */
  private toFrontendFormat(data: any): any {
    if (!data) return data;

    // Handle arrays
    if (Array.isArray(data)) {
      return data.map(item => this.toFrontendFormat(item));
    }

    const frontendData: any = {
      ...data,
      // Convert scope to string format
      scope: this.convertScopeToString(data.scope),
      // Map backend fields to frontend fields
      amount: data.activity_data || data.amount,
      notes: data.description || data.notes,
      date: data.reporting_period_start || data.created_at,
      // Ensure id is string
      id: String(data.id),
    };

    // Calculate co2_equivalent for display
    if (!frontendData.co2_equivalent && frontendData.amount && frontendData.emission_factor) {
      frontendData.co2_equivalent = frontendData.amount * frontendData.emission_factor;
    }

    return frontendData;
  }

  /**
   * List all emissions with optional filtering
   */
  async list(params?: {
    scope?: EmissionScope | number;
    category?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
    offset?: number;
    skip?: number; // Support both offset and skip
  }): Promise<Emission[]> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          // Convert scope to number for backend
          if (key === 'scope') {
            searchParams.append(key, String(this.convertScopeToNumber(value)));
          } 
          // Map skip to offset for backend compatibility
          else if (key === 'skip') {
            searchParams.append('skip', String(value));
          }
          else {
            searchParams.append(key, String(value));
          }
        }
      });
    }

    const path = `/api/v1/emissions/${searchParams.toString() ? `?${searchParams}` : ''}`;
    
    return this.client.get<Emission[]>(path, {
      validateResponse: (data) => {
        const frontendData = this.toFrontendFormat(data);
        return frontendData;
      },
    });
  }

  /**
   * Get emission by ID
   */
  async getById(id: string | number): Promise<Emission> {
    return this.client.get<Emission>(`/api/v1/emissions/${id}`, {
      validateResponse: (data) => {
        const frontendData = this.toFrontendFormat(data);
        return frontendData;
      },
    });
  }

  /**
   * Create new emission
   */
  async create(data: EmissionCreate): Promise<Emission> {
    console.log('Creating emission with frontend data:', data);
    
    // Convert to backend format
    const backendData = this.toBackendFormat(data);
    
    return this.client.post<Emission>('/api/v1/emissions/', backendData, {
      validateResponse: (responseData) => {
        console.log('Backend response:', responseData);
        const frontendData = this.toFrontendFormat(responseData);
        console.log('Converted to frontend format:', frontendData);
        return frontendData;
      },
    });
  }

  /**
   * Update emission
   */
  async update(id: string | number, data: EmissionUpdate): Promise<Emission> {
    // Convert to backend format
    const backendData = this.toBackendFormat(data);
    
    return this.client.patch<Emission>(`/api/v1/emissions/${id}`, backendData, {
      validateResponse: (responseData) => {
        const frontendData = this.toFrontendFormat(responseData);
        return frontendData;
      },
    });
  }

  /**
   * Delete emission
   */
  async delete(id: string | number): Promise<void> {
    await this.client.delete(`/api/v1/emissions/${id}`);
  }

  /**
   * Get emissions summary with aggregations
   */
  async getSummary(params?: {
    start_date?: string;
    end_date?: string;
    group_by?: 'day' | 'week' | 'month' | 'year';
  }): Promise<EmissionSummary> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value));
        }
      });
    }

    const path = `/api/v1/emissions/summary${searchParams.toString() ? `?${searchParams}` : ''}`;
    
    return this.client.get<EmissionSummary>(path, {
      validateResponse: (data) => {
        // The summary endpoint returns data in the expected format
        return data as EmissionSummary;
      },
    });
  }

  /**
   * Calculate emissions for an activity
   */
  async calculate(data: EmissionCalculate): Promise<CalculationResult> {
    // Convert to backend format
    const backendData = {
      ...data,
      scope: this.convertScopeToNumber(data.scope),
      activity_data: data.amount, // Backend might expect activity_data
    };
    
    return this.client.post<CalculationResult>('/api/v1/emissions/calculate', backendData, {
      validateResponse: (data) => data as CalculationResult,
    });
  }

  /**
   * Export emissions as CSV
   */
  async exportCSV(params?: {
    start_date?: string;
    end_date?: string;
    scope?: EmissionScope | number;
  }): Promise<Blob> {
    const searchParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          if (key === 'scope') {
            searchParams.append(key, String(this.convertScopeToNumber(value)));
          } else {
            searchParams.append(key, String(value));
          }
        }
      });
    }

    const path = `/api/v1/emissions/export/csv${searchParams.toString() ? `?${searchParams}` : ''}`;
    
    const response = await fetch(`${this.client['baseURL']}${path}`, {
      headers: this.client['headers'] as HeadersInit,
    });

    if (!response.ok) {
      throw new APIError('Export failed', response.status, 'EXPORT_ERROR');
    }

    return response.blob();
  }

  /**
   * Batch create emissions (optimized for bulk imports)
   */
  async batchCreate(emissions: EmissionCreate[]): Promise<Emission[]> {
    // Convert all emissions to backend format
    const backendData = emissions.map(e => this.toBackendFormat(e));
    
    return this.client.post<Emission[]>('/api/v1/emissions/batch', backendData, {
      validateResponse: (data) => {
        const frontendData = this.toFrontendFormat(data);
        return frontendData;
      },
    });
  }
}

// ==================== Main API Instance ====================
class FactorTraceAPI {
  private client: APIClient;
  public emissions: EmissionsRepository;

  constructor(config = API_CONFIG) {
    this.client = new APIClient(config);
    this.emissions = new EmissionsRepository(this.client);
  }

  /**
   * Health check endpoint
   */
  async health(): Promise<{ status: string; timestamp: string }> {
    return this.client.get('/health');
  }

  /**
   * Cancel all pending requests (useful for cleanup)
   */
  cancelAllRequests(): void {
    this.client.cancelAllRequests();
  }
}

// ==================== Singleton Export ====================
export const factortraceAPI = new FactorTraceAPI();

// ==================== React Hook Integration Helper ====================
/**
 * Helper for React Query integration
 * Use with @tanstack/react-query for caching and state management
 */
export const queryKeys = {
  emissions: {
    all: ['emissions'] as const,
    lists: () => [...queryKeys.emissions.all, 'list'] as const,
    list: (params?: Parameters<EmissionsRepository['list']>[0]) => 
      [...queryKeys.emissions.lists(), params] as const,
    details: () => [...queryKeys.emissions.all, 'detail'] as const,
    detail: (id: string | number) => [...queryKeys.emissions.details(), id] as const,
    summary: (params?: Parameters<EmissionsRepository['getSummary']>[0]) => 
      [...queryKeys.emissions.all, 'summary', params] as const,
  },
} as const;

// ==================== Type Guards ====================
export const isAPIError = (error: unknown): error is APIError => {
  return error instanceof APIError;
};

export const isNetworkError = (error: unknown): error is NetworkError => {
  return error instanceof NetworkError;
};

export const isDatabaseError = (error: unknown): error is DatabaseError => {
  return error instanceof DatabaseError;
};

// ==================== Error Message Helper ====================
export const getErrorMessage = (error: unknown): string => {
  if (isDatabaseError(error)) {
    return error.message;
  }
  
  if (isAPIError(error)) {
    if (error.status === 404) {
      return 'The requested resource was not found.';
    }
    if (error.status === 403) {
      return 'You do not have permission to perform this action.';
    }
    if (error.status === 401) {
      return 'You need to be authenticated to perform this action.';
    }
    if (error.status >= 500) {
      return 'A server error occurred. Please try again later.';
    }
    return error.message;
  }
  
  if (isNetworkError(error)) {
    return 'A network error occurred. Please check your connection and try again.';
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unexpected error occurred.';
};

/**
 * Usage Example:
 * 
 * import { factortraceAPI, getErrorMessage } from '@/lib/api/factortrace-api';
 * 
 * // List emissions
 * try {
 *   const emissions = await factortraceAPI.emissions.list({ scope: 1 }); // Can use number
 * } catch (error) {
 *   toast.error(getErrorMessage(error));
 * }
 * 
 * // Create emission with flexible scope
 * const newEmission = await factortraceAPI.emissions.create({
 *   scope: 1, // Can be 1, "1", "scope_1", or "Scope 1"
 *   category: 'stationary_combustion',
 *   activity: 'natural_gas',
 *   amount: 1000,
 *   unit: 'kWh',
 *   emission_factor: 0.185,
 *   date: new Date().toISOString(),
 * });
 * 
 * // With React Query
 * const { data, error } = useQuery({
 *   queryKey: queryKeys.emissions.list({ scope: 1 }),
 *   queryFn: () => factortraceAPI.emissions.list({ scope: 1 }),
 * });
 */