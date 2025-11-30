// src/lib/api-client.ts
// Type-safe API client using openapi-fetch

import createClient from "openapi-fetch";
import type { paths, components } from "../types/backend-schema";

// Create the typed client
const client = createClient<paths>({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
});

// Export typed schema helpers
export type EmissionCreate = components["schemas"]["EmissionCreate"];
export type EmissionResponse = components["schemas"]["EmissionResponse"];
export type EmissionsSummary = components["schemas"]["EmissionsSummary"];
export type EmissionUpdate = components["schemas"]["EmissionUpdate"];

// Export the client for direct use
export { client };
