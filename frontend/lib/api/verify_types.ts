import { EmissionCreate } from "./client";

// This object MUST match the backend schema exactly.
// If I misspell "scope" as "scopes", TypeScript will scream.
const testPayload: EmissionCreate = {
  scope: 1,
  category: "Mobile Combustion",
  activity_type: "Diesel",
  country_code: "DE",
  activity_data: 1000,
  unit: "liters"
};

console.log("Types are valid!");
