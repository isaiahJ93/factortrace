import createClient from "openapi-fetch";
import type { paths } from "./schema"; // The file you just generated

// Create the typed client
export const client = createClient<paths>({
  baseUrl: "http://127.0.0.1:8000", 
  // In production, this would be process.env.NEXT_PUBLIC_API_URL
});

// Helper to get the Types easily in our components
export type EmissionCreate = paths["/api/v1/emissions/"]["post"]["requestBody"]["content"]["application/json"];
export type EmissionResponse = paths["/api/v1/emissions/"]["post"]["responses"][200]["content"]["application/json"];
export type EmissionsSummary = paths["/api/v1/emissions/summary"]["get"]["responses"][200]["content"]["application/json"];
