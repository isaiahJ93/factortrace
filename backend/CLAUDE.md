# FactorTrace – Regulatory Compliance Engine

## 1. High-Level Context

FactorTrace is a **voucher-led, supplier-facing Scope 3 and sustainability reporting engine**.

Core goals:

- Automate **CSRD/ESRS-aligned Scope 3** reporting for Tier 1 & Tier 2 suppliers.
- Generate **PDF + XHTML/iXBRL** reports from structured data + emission factors.
- Support **multi-regime expansion**: CBAM, ISSB, EUDR, FuelEU, etc.
- Provide **voucher + credit-based** workflows for suppliers and their buyers.
- Over time, extend into a broader **global regulatory SaaS** platform.

---

## 2. Architecture Overview

### Backend

- Python, FastAPI (`app/main.py`, `app/api/v1`)
- Pydantic for schemas (`app/schemas`)
- SQLAlchemy ORM models (`app/models`)
- Alembic for migrations
- Emission factor storage in `emission_factors` table
- Ingestion scripts in `scripts/` and `data/`

### Database

- Local dev: SQLite (`sqlite:///./factortrace.db`)
- Production target: PostgreSQL
- Key tables (present or planned):
  - `users`
  - `emissions`
  - `vouchers`
  - `payments`
  - `reports`
  - `emission_factors`
- `emission_factors` holds DEFRA, EPA, EXIOBASE and other datasets with:
  - `dataset`, `scope`, `category`, `activity_type`
  - `country_code`, `year`
  - `factor`, `unit`, `metadata` (JSON)

### Frontend

- React/Next.js app ("frontend" directory)
- Talks to backend via `/api/v1/...`
- Will host:
  - CSV uploader
  - FactorTrace dashboard
  - Report generation + voucher flows
  - Later: multi-regime report selection (CSRD, CBAM, etc.)

---

## 3. Multi-Tenant Isolation (CRITICAL)

**Assume FactorTrace is multi-tenant.** Every query must be tenant-scoped.

### Rules

- Every "owned" entity (emissions, vouchers, payments, reports, etc.) must have a `tenant_id`.
- Backend must **never** return cross-tenant data.
- `tenant_id` is carried in the auth layer (JWT) and exposed via `current_user`.

### Backend Query Rules

When generating or modifying backend code:

- Always include tenant filters like:
```python
query = (
    db.query(Emission)
    .filter(Emission.tenant_id == current_user.tenant_id)
)
```

- For UPDATE / DELETE, also filter by tenant_id:
```python
record = (
    db.query(Emission)
    .filter(
        Emission.id == emission_id,
        Emission.tenant_id == current_user.tenant_id,
    )
    .first()
)
```

- Do not add new models that represent tenant-owned data without a `tenant_id` column.
- Shared reference tables (e.g. `emission_factors`) typically do not have `tenant_id`.

### Security Testing

Security tests must:
- Create data for Tenant A and Tenant B.
- Assert Tenant A cannot read, update or delete Tenant B's records.
- Assert list endpoints only return data scoped to `current_user.tenant_id`.

---

## 4. Coding Standards

- Use FastAPI conventions (APIRouter, dependency injection with Depends).
- Use Pydantic (project's current version) for schemas.
- Always add typing annotations.
- All new logic must have tests in `tests/`:
  - Services: `tests/services/...`
  - Endpoints: `tests/api/...`

### Emission Factor Access

Use `app/services/emission_factors.py` as the central access layer.

Do not query `emission_factors` directly from route handlers unless absolutely necessary.

Preferred API:
```python
from app.services.emission_factors import get_factor

factor = get_factor(
    db,
    scope=scope,
    category=category,
    activity_type=activity_type,
    country_code=country_code,
    year=year,
    dataset=dataset,
)
```

`get_factor` is responsible for:
- Fallbacks (e.g. country → GLOBAL)
- Dataset scoping (DEFRA / EPA / EXIOBASE)
- Basic sanity checks.

---

## 5. CSV Importer Requirements

FactorTrace must be comfortable with messy spreadsheets.

### Functional Requirements

- Support uploads of:
  - DEFRA-style CSVs
  - EPA-style CSVs
  - EXIOBASE-derived / client CSVs
- Map arbitrary column names to internal fields via a mapping layer (YAML and/or UI).

### Validation before ingestion:

- Required columns present (e.g. date, activity value, unit, category).
- Activity data numeric.
- Units are known & convertible.
- Dataset / scope / category mappings are valid.

### Error handling:

- Don't crash on bad data.
- Return structured error objects instead of throwing:
```json
{
  "row": 123,
  "column": "Unit",
  "message": "Unknown unit 'Tons'"
}
```

- UI should show errors in a table under the uploader.

### Localization / Formatting

Number formats:
- US: 1,234.56
- EU: 1.234,56

Date formats:
- YYYY-MM-DD
- DD/MM/YYYY
- MM/DD/YYYY (if necessary)

There should be a clear normalization layer (pure functions) so behavior is testable and reusable.

### File Size & Limits

- Reject or stream-process files > 50 MB.
- Show a clear message if the file is too large.
- For large files, avoid blocking the UI: use streaming / background tasks.

---

## 6. Unit & Currency Conversion

### Units

- Use the Pint library for unit normalization.
- Internal canonical units (examples):
  - Energy: kWh, MJ
  - Distance: km
  - Mass: kg
  - Volume: L
- All incoming units must be converted to canonical units before applying factors.

CSV importer must sanitize user input (locale formats) before converting to floats or handing off to Pint.

### Currency

For spend-based factors (EXIOBASE etc.):
- Normalize spend to EUR internally (unless explicitly configured otherwise).
- Use a single FX conversion source per run (ECB historical/API or a pluggable layer).
- Track metadata:
  - `original_currency`
  - `conversion_rate`
  - `conversion_date` (or period)

This metadata must be stored alongside normalized spend for auditability.

---

## 7. Emission Factor Datasets

Currently integrated / planned:

### DEFRA 2024

- Flat-file CSV mapped via YAML (`data/mappings/defra_2024.yml`).
- Country: GB
- Method: average_data
- Regulation: GHG_PROTOCOL
- Typical structure includes:
  - Activity name
  - kgCO₂e per unit (or per kWh, km, L, etc.)

### EPA GHG Emission Factors Hub 2024

- Cleaned CSV (`data/raw/epa_2024_hub_clean.csv`) based on official XLSX.
- Country: US
- Method: average_data
- Regulation: GHG_PROTOCOL
- Includes stationary combustion, fuels, etc.

### EXIOBASE 3 (2020 spend-based)

- Used for spend-based Scope 3 factors.
- Dataset name: EXIOBASE_2020
- Category: spend_based
- Scope: SCOPE_3
- Internal units: kgCO2e / EUR (or equivalent canonical spend unit).
- Covers multiple regions / countries with sector-level factors.

### Ingestion Rules

All dataset ingestion should:
- Use YAML mapping files in `data/mappings/`.
- Prefer the generic ingestion script (`scripts/ingest_factors_generic.py`) when possible.
- Log:
  - Dataset name
  - Inserted / updated / skipped rows
  - Any parsing errors
- Do not hardcode large tables inside Python modules (only small snippets for tests/sanity).

---

## 8. Deployment Standards

Target: Containerized FastAPI + Postgres.

### Backend

- Entry point: `app.main:app`
- Use Uvicorn/Gunicorn in production, e.g.:
```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app
```

- Respect environment variables:
  - `DATABASE_URL`
  - `ENVIRONMENT` (development / staging / production)
  - `CORS_ORIGINS`
- Healthcheck endpoint must be stable: `/api/v1/health`

### Docker

- Separate images for:
  - Backend API
  - (Optional) worker / scheduled tasks
- Use non-root user where possible.
- Run DB migrations on startup:
```bash
alembic upgrade head
```

(or via a dedicated migration init container).

---

## 9. Testing & Quality Gates

Always add tests for:
- New emission factor ingestion logic.
- New CSV mapping rules.
- Multi-tenant security (no cross-tenant leaks).

For bigger refactors, run:
- `pytest`
- Any custom integration scripts (e.g. EXIOBASE coverage tests).

Tests should cover:
- Happy path.
- Edge cases (missing factors, bad units, malformed CSV).
- Security cases (tenant isolation).

---

## 10. How to Work With This Project (for Claude / agents)

When editing or generating code:
- Respect multi-tenancy: always consider `tenant_id`.
- Don't bypass services:
  - Use service layers like `emission_factors.py` instead of duplicating queries.
- Prefer small, testable functions:
  - Especially for CSV import, unit conversion, and factor lookups.
- Never silently swallow errors:
  - Log them and return structured error info to the caller.

This file (CLAUDE.md) is the source of truth for how FactorTrace should evolve.

---

## 11. Domain Knowledge, Gotchas & Common Commands

FactorTrace operates in a specific regulatory and technical domain. Keep these constraints in mind.

### Regulatory / Domain Gotchas

- **DEFRA Update Cadence**
  - DEFRA emission factors are updated periodically (at least annually).
  - Ingestion must support versioned datasets (e.g. defra_2024, defra_2025) and avoid overwriting historical factors.

- **Spreadsheet Encoding**
  - Client and regulatory spreadsheets may use non-UTF-8 encodings (e.g. ISO-8859-1).
  - CSV import code must handle encoding errors gracefully when reading with Pandas.

- **Spend-Based Factors (EXIOBASE)**
  - EXIOBASE and similar datasets require FX normalization to EUR before applying kgCO₂e/EUR factors.
  - Store metadata: `original_currency`, `conversion_rate`, and `conversion_date` alongside normalized values.

### Technical / User Gotchas

- **UI Freeze on Large Files**
  - Never run heavy CSV validation synchronously on the main UI thread.
  - For large files (10k+ rows or tens of MB), use background tasks or Web Workers and stream progress back to the UI.

- **EU vs US Number Formats**
  - Importer must detect and normalize:
    - EU: 1.234,56 → 1234.56
    - US: 1,234.56 → 1234.56
  - Normalization should happen before converting to Python floats or handing to pint.

### Common Development Commands

- Run API locally:
```bash
poetry run uvicorn app.main:app --reload
```

- Run tests:
```bash
poetry run pytest -v
```

- Create DB migration:
```bash
alembic revision --autogenerate -m "describe change"
```

- Apply DB migrations:
```bash
alembic upgrade head
```
