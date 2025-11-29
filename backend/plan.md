# FactorTrace – Implementation Plan (V1 Production & Beyond)

This plan tracks the major phases to get FactorTrace from “engine works” to a **production-grade global regulatory SaaS** for Tier 1 & 2 suppliers.

---

## 0. Baseline & Tooling (DONE / KEEP STABLE)

**Goal:** Have a clean, assisted dev environment where Claude can work reliably.

- [x] `CLAUDE.md` with architecture, multi-tenancy rules, datasets, and scientific stack.
- [x] `.claudeignore` to exclude huge logs, data files, and build artifacts.
- [x] `.claude/commands`:
  - `/csv-debug` for ingestion/import debugging.
  - `/tenant-check` for multi-tenancy audits.
  - `/emission-test` for emission factor tests.
  - `/dockerize` for deployment artefacts.
- [x] `.mcp.json` stub for GitHub integration (token later).
- [ ] (Optional later) `.claude/skills` for automatic regulatory/CSV behaviors.

> **Rule:** Don’t waste time tweaking tooling unless you hit a real pain point. The current setup is “good enough” to ship V1.

---

## 1. Multi-Tenancy & Security Hardening (CRITICAL – DO FIRST)

**Goal:** Bulletproof tenant isolation so no customer can ever see another’s data.

### 1.1 Models & Auth

- [ ] Add `tenant_id` (string, indexed) to all tenant-owned models:
  - `User` (if not already).
  - `Emission` / `Emissions`.
  - `Voucher`.
  - `Payment`.
  - `Report` / `EmissionReport`.
- [ ] Ensure `tenant_id` is:
  - Set at user creation.
  - Carried in the JWT payload.
  - Exposed via `current_user.tenant_id` in dependencies.

### 1.2 Query Enforcement

- [ ] Run `/tenant-check` on:
  - `app/api/v1/endpoints/emissions.py`
  - `app/api/v1/endpoints/vouchers.py`
  - `app/api/v1/endpoints/payments.py`
  - Any other endpoints touching tenant-owned data.
- [ ] For **every** query (GET/POST/PUT/DELETE):
  - Add `.filter(Model.tenant_id == current_user.tenant_id)`.
  - For UPDATE/DELETE, filter **by id + tenant_id**.

### 1.3 Security Tests

- [ ] Create `tests/test_security.py` with:
  - Tenant A + Tenant B seeded data.
  - Tests asserting:
    - Tenant A cannot read Tenant B rows.
    - List endpoints only return current tenant data.
    - Writes/updates/deletes are tenant-scoped.

### 1.4 Optional Hardening

- [ ] Add a pre-commit hook to block commits with queries missing `tenant_id` filter.
- [ ] Add logging for access-denied events (for audit trail).

> **Exit Criteria (Phase 1):**  
> All tests pass, `/tenant-check` returns clean, and you are comfortable calling the backend **multi-tenant production-ready**.

---

## 2. Scientific Engine & Core Calculation (ADVANCED STACK)

**Goal:** Lock in a robust scientific foundation so you’re not patching maths later.

### 2.1 Libraries & Canonical Units

- [ ] Ensure the following are installed and wired:
  - `pint` – unit normalization.
  - `numpy` / `pandas` – core data handling.
  - `scipy` – uncertainty, distributions, Monte Carlo-style logic.
  - `xarray` / `pymrio` – for IO tables / EXIOBASE-style matrices (even if used lightly at first).
  - `currencyconverter` or equivalent FX library – spend normalization.
- [ ] Define **canonical units** in one place:
  - Mass: `kg`
  - Distance: `km`
  - Energy: `kWh` and/or `MJ`
  - Volume: `L`
  - Spend: `EUR`

### 2.2 Emissions Calculation Service

- [ ] Centralize calculation logic in a service module (e.g., `app/services/emissions_calculator.py`):
  - [ ] Takes **activity data + factor** and returns `kgCO2e` (and optionally `CO2e per unit`).
  - [ ] Uses `pint` to normalize raw units into canonical units before applying factors.
  - [ ] Handles **Scope 1, 2, and 3** (at least high-level).
- [ ] Add **uncertainty hooks** (even if basic at first):
  - [ ] Support simple ranges or standard deviation on factors.
  - [ ] Use `scipy` for basic propagation / Monte Carlo where appropriate later.

### 2.3 Tests

- [ ] Add `tests/test_emissions_calculator.py`:
  - [ ] Unit conversion sanity checks (e.g. `L` → `kg` via density for fuels, `kWh` ↔ `MJ`).
  - [ ] Correct factor application for DEFRA, EPA, EXIOBASE examples.
  - [ ] Edge cases: zero/negative values, missing units, invalid units.

> **Exit Criteria (Phase 2):**  
> You trust the calculation engine’s behavior enough to expose it to paying customers.

---

## 3. Emission Factor Ingestion (DEFRA, EPA, EXIOBASE & FUTURE DATASETS)

**Goal:** Have a generic, repeatable ingestion pipeline that can take any emission factor dataset and map it into `emission_factors`.

### 3.1 Ingestion Strategy

- [ ] Use a **generic ingestion script** (e.g. `scripts/ingest_factors_generic.py`) that:
  - [ ] Reads `data/raw/*.csv` or XLSX.
  - [ ] Uses YAML mapping files in `data/mappings/*.yml` to map columns → standard fields.
  - [ ] Writes into `emission_factors` with consistent fields.

### 3.2 Datasets

- [ ] **DEFRA 2024**
  - [ ] Clean/final CSV in `data/raw/defra_2024_clean.csv`.
  - [ ] YAML mapping e.g. `data/mappings/defra_2024.yml`.
- [ ] **EPA GHG Hub 2024**
  - [ ] Clean CSV e.g. `epa_2024_hub_clean.csv`.
  - [ ] Mapping file `epa_2024.yml`.
- [ ] **EXIOBASE 3 (2020) Spend-Based**
  - [ ] Raw data in `data/raw/exiobase_2020_*`.
  - [ ] Mapping file `exiobase_2020.yml`.
  - [ ] Ensure units align to `kgCO2e / EUR`.

### 3.3 Ingestion Tests

- [ ] Add `tests/test_ingestion_defra.py`, `test_ingestion_epa.py`, `test_ingestion_exiobase.py`:
  - [ ] Verify expected row counts (min thresholds).
  - [ ] Verify no negative factors.
  - [ ] Verify scopes/categories/dataset names are correct.
  - [ ] Ensure `GLOBAL` and key country codes (US, DE, CN, GB, etc.) exist where expected.

> **Exit Criteria (Phase 3):**  
> You can confidently re-run ingestion whenever datasets are updated and trust the factor table.

---

## 4. CSV Importer Boss Fight (User-Facing Data Ingestion)

**Goal:** Let non-technical users upload messy spreadsheets and turn them into clean, validated emissions records.

### 4.1 File Upload & Limits

- [ ] Implement upload endpoint(s) with:
  - [ ] File size limit (e.g. 50MB).
  - [ ] Clear error message for oversized files.
  - [ ] Support for CSV + basic Excel (.xlsx/.xls).
  - [ ] Encoding handling (UTF-8, ISO-8859-1).

### 4.2 Column Mapping Layer

- [ ] Implement a mapping model:
  - [ ] Arbitrary client column name → internal field (`date`, `activity_value`, `unit`, `currency`, `category`, etc.).
  - [ ] Store mappings per tenant (so they can reuse templates).
- [ ] Frontend:
  - [ ] Auto-detect headers from upload.
  - [ ] Drag-and-drop or dropdown mapping UI.
  - [ ] Preview first 10 rows with mapped columns.
  - [ ] Save mapping state to localStorage / DB for resume.

### 4.3 Sanitization & Validation

- [ ] Number handling:
  - [ ] Detect EU (`1.234,56`) vs US (`1,234.56`) formats.
  - [ ] Normalize to `1234.56` before numeric conversion.
- [ ] Units:
  - [ ] Validate with `pint` (reject unknown units).
  - [ ] Convert to canonical units.
- [ ] Currency:
  - [ ] Validate ISO 4217 codes.
  - [ ] Use FX library to normalize to EUR.
- [ ] Dates:
  - [ ] Accept `YYYY-MM-DD`, `DD/MM/YYYY`, `MM/DD/YYYY` (if needed).
  - [ ] Normalize to ISO.

### 4.4 Error Reporting

- [ ] Backend returns **structured error objects** like:
  - `{ "row": 123, "column": "Unit", "value": "Tons", "message": "Unknown unit" }`
- [ ] Frontend displays:
  - [ ] Table under uploader with row/column/error.
  - [ ] Totals: number of rows valid vs invalid.
- [ ] Optional:
  - [ ] “Fix automatically” suggestions for common issues (e.g. unit aliasing).

### 4.5 CSV Import Tests

- [ ] Add `tests/test_csv_importer.py`:
  - [ ] Valid file → successful import.
  - [ ] Malformed file → structured errors, no crash.
  - [ ] Mixed EU/US number formats.
  - [ ] Oversized file → proper rejection.

> **Exit Criteria (Phase 4):**  
> A typical procurement/sustainability manager can upload their sheet, fix a few red cells, and **get a valid import without needing you on a call**.

---

## 5. Reporting, iXBRL & Multi-Regime Expansion

**Goal:** Turn calculated emissions into **saleable outputs**: CSRD/ESRS E1 reports, plus other regimes over time.

### 5.1 CSRD/ESRS Scope 3 Reporting (Initial V1)

- [ ] Implement a report generation service:
  - [ ] Uses Jinja2 templates to generate PDF-ready HTML.
  - [ ] Exports:
    - [ ] PDF (WeasyPrint or similar).
    - [ ] XHTML/iXBRL with correct ESRS E1 tagging.
- [ ] Map emissions and meta-data to ESRS fields:
  - [ ] Scope 1, 2, 3 breakdown.
  - [ ] Intensity metrics.
  - [ ] Uncertainty / data quality tiers.

### 5.2 Multi-Regime Hooks (Design, not full build yet)

- [ ] Design entities and fields such that:
  - [ ] Adding CBAM, ISSB, EUDR, FuelEU later reuses underlying data.
  - [ ] A **single voucher/credit** can eventually generate multiple report types.
- [ ] Add stubs/placeholders for:
  - [ ] CBAM report generator.
  - [ ] ISSB sustainability disclosures.
  - [ ] EUDR / deforestation-related fields where relevant.

> Full implementation of these can be Phase 6+, but the data model and architecture should **not block** expansion.

---

## 6. Deployment, Ops & Commercial Readiness

**Goal:** Be able to run this as a **real SaaS** for paying customers.

### 6.1 Deployment

- [ ] Use `/dockerize` command to generate/refine:
  - [ ] `Dockerfile` (FastAPI backend).
  - [ ] `docker-compose.yml` with:
    - Backend.
    - Postgres.
    - Optional migration/init service.
- [ ] Ensure:
  - [ ] `DATABASE_URL`, `ENVIRONMENT`, `CORS_ORIGINS` are environment-driven.
  - [ ] Healthcheck route: `/api/v1/health`.
  - [ ] Start-up runs `alembic upgrade head` safely.

### 6.2 Monitoring & Logs

- [ ] Add structured logging (JSON logs, at least for errors).
- [ ] Add basic metrics hooks (requests, errors, latency).
- [ ] Plan for Sentry / error monitoring integration later.

### 6.3 Commercial Layer

- [ ] Implement **credit-based** pricing:
  - [ ] 5 credits = X reports for €1,500, etc.
- [ ] Ensure:
  - [ ] Usage tracking per tenant.
  - [ ] Payment + invoice hooks (even if manual initially).
  - [ ] Basic admin dashboard for you to see who is doing what.

---

## 7. Later / Strategic Phases (Not Needed for V1)

These are **deliberately postponed** to avoid scope creep now:

- [ ] ML-based anomaly detection on activity data.
- [ ] CUDA-accelerated large-scale Monte Carlo simulations.
- [ ] Federated learning and on-prem “black box” deployments.
- [ ] Digital product passports at full scale (beyond initial hooks).
- [ ] Tenant-level analytics with heavy time-series/OLAP infra.

---

## Current Focus (Right Now)

1. **Finish Phase 1: Multi-Tenancy & Security** (no excuses).
2. **Lock in Phase 2: Scientific Engine** (no maths regret later).
3. **Enter Phase 4: CSV Importer Boss Fight** (this is where buyers feel the value).

Everything else is secondary until those three are real and tested.

