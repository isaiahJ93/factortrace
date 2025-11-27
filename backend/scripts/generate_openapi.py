#!/usr/bin/env python3
"""
OpenAPI Specification Generator for FactorTrace API

Generates a complete OpenAPI 3.1 specification file (openapi.json) from the
FastAPI application. This spec can be used for:
- Frontend code generation (TypeScript types)
- API documentation hosting (Swagger UI, Redoc)
- Client SDK generation
- API testing tools (Postman, Insomnia)

Usage:
    python scripts/generate_openapi.py

Output:
    openapi.json - Complete OpenAPI 3.1 specification
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ANSI colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def generate_openapi_spec():
    """Generate OpenAPI specification from FastAPI app."""
    print(f"\n{CYAN}{BOLD}{'='*60}{RESET}")
    print(f"{CYAN}{BOLD}   FACTORTRACE OPENAPI SPEC GENERATOR{RESET}")
    print(f"{CYAN}{BOLD}{'='*60}{RESET}\n")

    print(f"{YELLOW}[1/3] Importing FastAPI application...{RESET}")

    try:
        from app.main import app
        print(f"{GREEN}✓ FastAPI app imported successfully{RESET}")
    except Exception as e:
        print(f"Error importing app: {e}")
        sys.exit(1)

    print(f"\n{YELLOW}[2/3] Generating OpenAPI schema...{RESET}")

    # Get the OpenAPI schema
    openapi_schema = app.openapi()

    # Enhance the schema with additional metadata
    openapi_schema["info"]["title"] = "FactorTrace API"
    openapi_schema["info"]["description"] = """
# FactorTrace - Enterprise Carbon Accounting Platform

FactorTrace is a bank-grade SaaS platform for GHG emissions management and
regulatory compliance reporting (ESRS, CDP, TCFD, SBTi).

## Key Features

- **Emissions Tracking**: Calculate and track Scope 1, 2, and 3 emissions
- **Database-backed Factors**: Region-specific emission factors from DEFRA, EPA, and custom sources
- **Regulatory Reporting**: Generate ESRS E1 compliant iXBRL reports
- **Data Quality**: GHG Protocol compliant uncertainty analysis

## Authentication

All endpoints require Bearer token authentication:
```
Authorization: Bearer <your_jwt_token>
```

Obtain a token via `POST /api/v1/auth/login`.

## Rate Limiting

- Standard tier: 100 requests/minute
- Enterprise tier: 1000 requests/minute

## Support

- Documentation: https://docs.factortrace.com
- Issues: https://github.com/factortrace/api/issues
"""
    openapi_schema["info"]["version"] = "1.0.0"
    openapi_schema["info"]["contact"] = {
        "name": "FactorTrace Support",
        "email": "support@factortrace.com",
        "url": "https://factortrace.com"
    }
    openapi_schema["info"]["license"] = {
        "name": "Proprietary",
        "url": "https://factortrace.com/terms"
    }

    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Local Development Server"
        },
        {
            "url": "https://api.factortrace.com",
            "description": "Production Server"
        },
        {
            "url": "https://staging-api.factortrace.com",
            "description": "Staging Server"
        }
    ]

    # Add tags with descriptions
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and token management"
        },
        {
            "name": "Emissions",
            "description": "Core emission tracking and calculation endpoints. Create, read, update, and delete emission records with automatic CO2e calculation."
        },
        {
            "name": "Emission Factors",
            "description": "Manage emission factors database. Search and retrieve region-specific emission factors."
        },
        {
            "name": "Reports",
            "description": "Generate compliance reports for ESRS, CDP, TCFD, and SBTi standards."
        },
        {
            "name": "ESRS E1",
            "description": "European Sustainability Reporting Standards (ESRS) E1 Climate Change disclosures and iXBRL export."
        },
        {
            "name": "Scope 3",
            "description": "Advanced Scope 3 value chain emissions calculation with category-specific methodologies."
        },
        {
            "name": "Data Quality",
            "description": "Data quality scoring and uncertainty analysis per GHG Protocol guidance."
        },
        {
            "name": "Health",
            "description": "API health and status endpoints"
        }
    ]

    # Count endpoints
    path_count = len(openapi_schema.get("paths", {}))
    schema_count = len(openapi_schema.get("components", {}).get("schemas", {}))

    print(f"{GREEN}✓ Schema generated successfully{RESET}")
    print(f"   - Paths: {path_count}")
    print(f"   - Schemas: {schema_count}")

    print(f"\n{YELLOW}[3/3] Writing openapi.json...{RESET}")

    # Write to file
    output_path = project_root / "openapi.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    # Calculate file size
    file_size = output_path.stat().st_size
    file_size_kb = file_size / 1024

    print(f"{GREEN}✓ OpenAPI spec written to: {output_path}{RESET}")
    print(f"   - File size: {file_size_kb:.1f} KB")

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{GREEN}{BOLD}✓ OPENAPI GENERATION COMPLETE{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    print(f"\n{CYAN}Next steps:{RESET}")
    print(f"  1. View in Swagger UI: http://localhost:8000/docs")
    print(f"  2. View in ReDoc: http://localhost:8000/redoc")
    print(f"  3. Import into Postman/Insomnia")
    print(f"  4. Generate TypeScript types with openapi-typescript")
    print(f"     npx openapi-typescript openapi.json -o frontend/src/api/types.ts\n")

    return openapi_schema


def print_summary(schema: dict):
    """Print a summary of the API endpoints."""
    print(f"\n{CYAN}{BOLD}API ENDPOINT SUMMARY{RESET}")
    print(f"{'-'*60}")

    paths = schema.get("paths", {})

    # Group by tags
    by_tag = {}
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                tags = details.get("tags", ["Untagged"])
                for tag in tags:
                    if tag not in by_tag:
                        by_tag[tag] = []
                    by_tag[tag].append({
                        "method": method.upper(),
                        "path": path,
                        "summary": details.get("summary", "No summary")
                    })

    for tag, endpoints in sorted(by_tag.items()):
        print(f"\n{BOLD}{tag}{RESET}")
        for ep in endpoints:
            method_color = {
                "GET": "\033[94m",     # Blue
                "POST": "\033[92m",    # Green
                "PUT": "\033[93m",     # Yellow
                "DELETE": "\033[91m",  # Red
                "PATCH": "\033[95m"    # Magenta
            }.get(ep["method"], "")
            print(f"  {method_color}{ep['method']:6}{RESET} {ep['path']}")
            print(f"         {ep['summary'][:50]}...")


if __name__ == "__main__":
    schema = generate_openapi_spec()
    print_summary(schema)
