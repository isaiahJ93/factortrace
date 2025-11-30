




Emissions API Contract



Contract-first spec for emissions-related endpoints.



All endpoints are tenant-scoped and must enforce tenant_id == current_user.tenant_id.









POST /api/v1/emissions



Purpose

Create a new emission record for the current tenant.



Request Body (JSON)



Required:





activity_value (string | number): Raw activity amount (e.g. "1234.56").

unit (string): Pint-compatible unit (e.g. "kg", "kWh", "L").

emission_factor_id (UUID): Foreign key to emission_factors.

date (string, ISO 8601): Date of activity (e.g. "2024-11-30").



Optional:





category (string): Scope/category label (e.g. "Scope 3 - Purchased Goods").

notes (string): Free-text notes.



Business Rules





tenant_id must be derived from current_user and not supplied by the client.

unit must be validated via Pint:



Reject unknown units with clear error + suggestion if possible.

activity_value must be:



Parsed via sanitize_number() to handle 1.234,56 vs 1,234.56.

Empty/invalid values rejected with row-level style errors where applicable.

emission_factor_id must exist and be compatible (unit dimension, scope/category).

calculated_co2e is computed and stored server-side.



Success Response (201)



{

  "id": "uuid",

  "tenant_id": "tenant_abc",

  "activity_value": 1234.56,

  "unit": "kg",

  "emission_factor_id": "uuid",

  "calculated_co2e": 456.78,

  "category": "Scope 3 - Purchased Goods",

  "date": "2024-11-30",

  "notes": "Optional note",

  "created_at": "2024-11-30T10:00:00Z",

  "updated_at": "2024-11-30T10:00:00Z"

}

Error Responses



422 Unprocessable Entity – validation errors:



{

  "detail": [

    {

      "field": "unit",

      "message": "Unknown unit 'tons'. Did you mean 'tonne'?"

    },

    {

      "field": "activity_value",

      "message": "Expected a number, got 'N/A'."

    }

  ]

}

403 Forbidden – cross-tenant or unauthorized access attempts.









GET /api/v1/emissions



Purpose

List emissions for the current tenant with pagination and filters.



Query Parameters





page (int, default 1)

page_size (int, default 25, max 100)

category (string, optional)

date_from (ISO date, optional)

date_to (ISO date, optional)



Business Rules





Always filter results by tenant_id == current_user.tenant_id.

Apply pagination.

Optional filtering by category and date range.



Success Response (200)



{

  "items": [

    {

      "id": "uuid",

      "activity_value": 1234.56,

      "unit": "kg",

      "calculated_co2e": 456.78,

      "category": "Scope 3 - Purchased Goods",

      "date": "2024-11-30"

    }

  ],

  "page": 1,

  "page_size": 25,

  "total": 123

}







GET /api/v1/emissions/{id}



Purpose

Return a single emission owned by the current tenant.



Business Rules





404 if not found or belongs to another tenant (do not leak existence).







PUT /api/v1/emissions/{id}



Purpose

Update an emission record for the current tenant.



Business Rules





Must load by id + tenant_id.

Recompute calculated_co2e if activity_value, unit, or emission_factor_id changes.

Audit fields (updated_at) must be written.







DELETE /api/v1/emissions/{id}



Purpose

Soft-delete an emission.



Business Rules





Must enforce tenant_id.

Soft delete via a flag or deleted_at timestamp (no hard delete in V1).

404 on cross-tenant or missing record.







Tests Required



Creation success (happy path).

Invalid unit → 422.

Invalid activity_value → 422.

Cross-tenant fetch/update/delete → 403/404.

Pagination behaviour (page limits).

Soft-deletion behaviour (deleted records don’t show in list).

