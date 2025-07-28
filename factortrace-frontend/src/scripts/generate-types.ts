import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

/**
 * Elite type generation from FastAPI OpenAPI schema
 */
async function generateTypesFromFastAPI() {
  // Fetch OpenAPI schema from FastAPI
  const response = await fetch('http://localhost:8000/openapi.json');
  const schema = await response.json();
  
  // Generate TypeScript types using openapi-typescript
  execSync('npx openapi-typescript http://localhost:8000/openapi.json -o ./src/types/generated-api.d.ts');
  
  // Generate React Query hooks
  execSync('npx openapi-codegen http://localhost:8000/openapi.json -o ./src/hooks/api');
  
  console.log('✅ Types generated from FastAPI schema');
}

