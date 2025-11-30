// src/services/emissionApi.ts
// Emissions API service using type-safe openapi-fetch client

import {
  client,
  type EmissionCreate,
  type EmissionResponse,
  type EmissionsSummary,
  type EmissionUpdate,
} from "../lib/api-client";

// Re-export types for convenience
export type { EmissionCreate, EmissionResponse, EmissionsSummary, EmissionUpdate };

/**
 * Create a new emission record
 * Automatically calculates CO2e based on emission factors
 */
export async function createEmission(
  data: EmissionCreate
): Promise<EmissionResponse> {
  const { data: result, error } = await client.POST("/api/v1/emissions/", {
    body: data,
  });

  if (error) {
    throw new Error(
      typeof error === "object" && "detail" in error
        ? String(error.detail)
        : "Failed to create emission"
    );
  }

  return result;
}

/**
 * List all emissions with optional filtering
 */
export async function getEmissions(params?: {
  scope?: number;
  category?: string;
  skip?: number;
  limit?: number;
}): Promise<EmissionResponse[]> {
  const { data, error } = await client.GET("/api/v1/emissions/", {
    params: { query: params },
  });

  if (error) {
    throw new Error(
      typeof error === "object" && "detail" in error
        ? String(error.detail)
        : "Failed to fetch emissions"
    );
  }

  // Ensure we always return an array
  return Array.isArray(data) ? data : [];
}

/**
 * Get aggregated emissions summary for dashboards
 */
export async function getEmissionsSummary(): Promise<EmissionsSummary> {
  const { data: result, error } = await client.GET("/api/v1/emissions/summary");

  if (error) {
    throw new Error(
      typeof error === "object" && "detail" in error
        ? String(error.detail)
        : "Failed to fetch emissions summary"
    );
  }

  return result;
}

/**
 * Get a single emission by ID
 */
export async function getEmission(id: number): Promise<EmissionResponse> {
  const { data: result, error } = await client.GET("/api/v1/emissions/{emission_id}", {
    params: { path: { emission_id: id } },
  });

  if (error) {
    throw new Error(
      typeof error === "object" && "detail" in error
        ? String(error.detail)
        : "Failed to fetch emission"
    );
  }

  return result;
}

/**
 * Update an existing emission record
 */
export async function updateEmission(
  id: number,
  data: EmissionUpdate
): Promise<EmissionResponse> {
  const { data: result, error } = await client.PUT("/api/v1/emissions/{emission_id}", {
    params: { path: { emission_id: id } },
    body: data,
  });

  if (error) {
    throw new Error(
      typeof error === "object" && "detail" in error
        ? String(error.detail)
        : "Failed to update emission"
    );
  }

  return result;
}

/**
 * Delete an emission record
 */
export async function deleteEmission(id: number): Promise<void> {
  const { error } = await client.DELETE("/api/v1/emissions/{emission_id}", {
    params: { path: { emission_id: id } },
  });

  if (error) {
    throw new Error(
      typeof error === "object" && "detail" in error
        ? String(error.detail)
        : "Failed to delete emission"
    );
  }
}

/**
 * Get emission factors for a category
 */
export async function getEmissionFactors(params?: {
  scope?: number;
  category?: string;
  country_code?: string;
}): Promise<unknown[]> {
  const { data, error } = await client.GET("/api/v1/emission-factors/", {
    params: { query: params },
  });

  if (error) {
    throw new Error(
      typeof error === "object" && "detail" in error
        ? String(error.detail)
        : "Failed to fetch emission factors"
    );
  }

  // Ensure we always return an array
  return Array.isArray(data) ? data : [];
}

/**
 * Get emission categories grouped by scope
 * @param scope - Optional scope number (1, 2, or 3) to filter categories
 */
export async function getEmissionCategories(scope?: number): Promise<string[]> {
  const { data, error } = await client.GET(
    "/api/v1/emission-factors/categories",
    { params: { query: { scope } } }
  );

  if (error) {
    throw new Error(
      typeof error === "object" && "detail" in error
        ? String(error.detail)
        : "Failed to fetch categories"
    );
  }

  // Ensure we always return an array
  if (Array.isArray(data)) {
    return data as string[];
  }
  return [];
}

/**
 * Activity factor type returned from the API
 */
export interface ActivityFactor {
  activity_type: string;
  unit: string;
  factor_value: number;
  source: string;
}

/**
 * Get available country codes from the database
 * Returns a sorted list with GLOBAL first, then alphabetically
 */
export async function getAvailableCountries(): Promise<string[]> {
  const { data, error } = await client.GET("/api/v1/emissions/countries");

  if (error) {
    throw new Error(
      typeof error === "object" && "detail" in error
        ? String(error.detail)
        : "Failed to fetch countries"
    );
  }

  // Ensure we always return an array
  if (Array.isArray(data)) {
    return data as string[];
  }
  return [];
}

/**
 * Get activity types (emission factors) for a specific category
 * @param category - The emission category to get activity types for
 */
export async function getActivityTypes(category: string): Promise<ActivityFactor[]> {
  const { data, error } = await client.GET(
    "/api/v1/emissions/factors",
    { params: { query: { category } } }
  );

  if (error) {
    throw new Error(
      typeof error === "object" && "detail" in error
        ? String(error.detail)
        : "Failed to fetch activity types"
    );
  }

  // Ensure we always return an array
  if (Array.isArray(data)) {
    return data as ActivityFactor[];
  }
  return [];
}
