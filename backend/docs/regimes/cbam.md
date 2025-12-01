# CBAM Regime Specification – FactorTrace

Status: Draft → Target V1 ready in 6–8 weeks  
Owner: Isaiah + Claude Agentic Coder  
Primary Users: Importers into EU, Tier 1–2 suppliers, customs/broker teams  

---

## 1. What CBAM Is (Working Model for the System)

CBAM = **Carbon Border Adjustment Mechanism**.  
We care about it as a **product-level embedded emissions + declaration workflow** for imports into the EU.

**Internal mental model for FactorTrace:**

- A **CBAM Declaration** =  
  > “For this period and this importer, here are the products (by CN code), quantities, embedded emissions (tCO₂e), and whether we use verified values or EU default factors.”

We don’t need to implement the entire regulation. We need a **90/10 productised subset** that:

1. Maps **CN product codes → sector/factor dataset** (EXIOBASE/DEFRA/EPA as needed)  
2. Calculates **embedded emissions / tonne or unit**  
3. Aggregates per:
   - Product code
   - Country of origin
   - Installation / facility (if applicable)
4. Generates a **CBAM-compatible report** we can:
   - Export as **XHTML/iXBRL**
   - Use as an **annex** to the official CBAM submission

---

## 2. Supported Scope in V1

### 2.1 Products / Sectors (Start Narrow, Expand)

V1 Product Focus (realistic wedge):

- Steel / iron products
- Aluminium
- Cement
- Fertilisers
- Electricity (if feasible)
- Hydrogen (optional V1.1)

These align with early CBAM scope and give us a **credible product** without boiling the ocean.

We **must** model products generically so we can add more CN codes later.

---

## 3. Data Model Additions

### 3.1 New Core Concepts

We extend the existing emissions & voucher model with CBAM-specific entities.

**New tables (conceptual):**

1. **cbam_product**
   - `id`
   - `cn_code` (8–10 chars)
   - `description`
   - `default_factor_id` (FK → emission_factor)
   - `unit` (e.g. tonne, kg, MWh)
   - `regime` = "CBAM"

2. **cbam_declaration**
   - `id`
   - `importer_tenant_id` (FK → tenant)
   - `period_start`, `period_end`
   - `declaration_reference` (string, user-supplied or generated)
   - `status` (draft / submitted / amended)
   - `total_embedded_emissions_tco2e`
   - `created_at`, `updated_at`

3. **cbam_declaration_line**
   - `id`
   - `declaration_id` (FK → cbam_declaration)
   - `cbam_product_id` (FK → cbam_product)
   - `facility_id` (nullable – FK → installation/facility table if we have one)
   - `country_of_origin` (ISO 2/3 code)
   - `quantity` (numeric)
   - `quantity_unit` (must match expected unit)
   - `embedded_emissions_tco2e` (calculated)
   - `emission_factor_id` (FK → emission_factor used in calc)
   - `is_default_factor` (bool – true if EU default used)
   - `evidence_reference` (link to PDF/doc in future)

4. **cbam_factor_source** (optional for traceability)
   - `id`
   - `dataset` (e.g. “EU_CBAM_DEFAULT”, “PLANT_SPECIFIC”, “EXIOBASE2020”)
   - `version`
   - `notes`

### 3.2 Re-use existing tables

We **reuse**:

- `emission_factors` (with new dataset values like `CBAM_DEFAULT`, `CBAM_PLANT`)
- Existing `Emission` / calculation services for:
  - Unit handling (Pint)
  - CO₂e conversion
  - Dataset metadata

---

## 4. Calculation Logic – CBAM Embedded Emissions

### 4.1 High-Level Workflow

For each **CBAM declaration line**:

1. Identify the **CBAM product** by `cn_code`
2. Load relevant **emission factor**:
   - If importer provides plant-specific data → use that factor
   - Else → fallback to **EU CBAM default** factor dataset
3. Normalize units:
   - Ensure `quantity_unit` matches factor’s `activity_unit`
4. Compute:
   - `embedded_emissions_tco2e = quantity * factor_value_tco2e_per_unit`
5. Store result on `cbam_declaration_line`
6. Roll up:
   - **Per product**
   - **Per country**
   - Total per declaration

### 4.2 Factor Datasets

We support:

- `dataset="CBAM_DEFAULT"` – EU default factors
- `dataset="CBAM_PLANT_SPECIFIC"` – importer/supplier-provided factors
- `dataset="EXIOBASE2020"` – fallback if we need sector-based approximation

**Claude must ensure:**

- All CBAM emissions are tagged with the dataset used
- Default vs specific factors clearly separated in the API & reports

---

## 5. API Design for CBAM

We will likely create a new API namespace:

Base path:

- `/api/v1/cbam/`

Endpoints (contract-first; Claude should generate OpenAPI + Pydantic schemas):

1. `POST /cbam/products/`
   - Create or register a CBAM product
   - Fields: `cn_code`, `description`, `default_factor_id`, `unit`

2. `GET /cbam/products/`
   - List products, filter by `cn_code` or partial match

3. `POST /cbam/declarations/`
   - Create draft declaration
   - Body:
     - `period_start`, `period_end`
     - `declaration_reference` (optional)
   - Returns declaration with `id`

4. `POST /cbam/declarations/{id}/lines/`
   - Add line items:
     - `cn_code`
     - `quantity`, `quantity_unit`
     - `country_of_origin`
     - optional: `facility_id`, `factor_dataset` override

5. `GET /cbam/declarations/{id}`
   - Full declaration:
     - lines
     - totals
     - breakdowns

6. `POST /cbam/declarations/{id}/calculate`
   - Trigger embedded emissions calculation
   - Idempotent; recomputes all lines based on current factors

7. `POST /cbam/declarations/{id}/export`
   - Generate CBAM report bundle:
     - `pdf_report_url`
     - `xhtml_ixbrl_url`
     - optional: `csv_export_url`

All endpoints are **tenant-scoped**:
- `tenant_id` inferred from auth
- Claude must ensure **no cross-tenant access**

---

## 6. Report Templates – CBAM

We reuse the report infrastructure used for ESRS, but with a **CBAM-specific template**.

### 6.1 Core sections

1. **Importer and period**
   - Importer name, VAT/ID
   - Period covered

2. **Summary table**
   - Per product (CN code):
     - `total_quantity`
     - `total_embedded_emissions`
     - `% using default factors`

3. **Country breakdown**
   - For each `country_of_origin`:
     - totals per product
     - high-level risk flag (optional later)

4. **Factor usage**
   - Table: factor dataset usage:
     - `CBAM_DEFAULT`, `CBAM_PLANT_SPECIFIC`, `EXIOBASE2020`
   - Emissions split per dataset

5. **Annex – line-level export**
   - CSV/XLSX style data for line-level detail

### 6.2 Output formats

- PDF (for humans)
- XHTML/iXBRL (for machine submission / archive)
- CSV (for broker/customs uploads)

Claude should:

- Create **Jinja2 templates** for CBAM
- Add corresponding export functions (similar to ESRS E1 export flow)

---

## 7. Validation & Edge Cases

Claude must add tests that cover:

1. Product not found:
   - `cn_code` not in `cbam_product` table → clear 4xx error

2. Missing factor:
   - No plant-specific factor and no default:
     - Either block the line or fallback strategy, but MUST be explicit

3. Unit mismatch:
   - `quantity_unit` incompatible with factor’s unit:
     - Use Pint to detect and either convert or error

4. Mixed datasets:
   - Declaration with both default and specific factors:
     - Ensure report clearly labels which lines use which dataset

5. Multi-country:
   - Same CN code from multiple origin countries:
     - Aggregations by both product and country

6. Large declarations:
   - 10k+ lines
   - Ensure performance tests exist and **respect PERFORMANCE_BUDGET.md**

---

## 8. UX / Workflow Expectations

We’re not designing pixel-perfect screens here, but Claude should assume:

- A **CBAM tab/section** in the UI:
  - List of declarations
  - “Create new declaration” wizard
- CSV upload option:
  - Import customs / broker export into CBAM lines
  - Map columns to:
    - CN code
    - Quantity
    - Country
    - Facility (optional)
- Status badges:
  - Draft / Ready / Exported

---

## 9. Integration with Existing System

Claude must wire CBAM into:

1. **Tenant isolation**:
   - CBAM data belongs to the same tenant model as CSRD

2. **Voucher model (future)**:
   - OEM can buy a “CBAM compliance pack” for suppliers
   - For now: leave hooks in the schema (e.g. `voucher_id` nullable on `cbam_declaration`)

3. **Regime abstraction (future)**:
   - This is the **first non-CSRD regime**
   - Design so EUDR/ISSB can plug in:
     - `regime` enums
     - shared reporting/export infrastructure

---

## 10. Expectations from Claude Agentic Coder

When given this file + the rest of the meta system, Claude should:

1. Propose or generate:
   - SQLAlchemy models for `cbam_product`, `cbam_declaration`, `cbam_declaration_line`
   - Alembic migration
2. Implement:
   - CBAM services module: `app/services/cbam.py` (or `cbam_service.py`)
   - API endpoints under `/api/v1/cbam`
3. Add:
   - Tests under `tests/test_cbam_*.py` covering calculations and API
4. Wire:
   - Report export utilizing existing XHTML/iXBRL export pattern
5. Respect:
   - `DECISIONS.md` (multi-tenancy, units)
   - `PERFORMANCE_BUDGET.md` (performance guardrails)
   - `LEARNINGS.md` (Pint, EXIOBASE usage patterns)

---

## 11. Non-Goals for V1

To keep CBAM shippable:

- No full-blown customs/broker integration in V1  
  (we can do CSV import + API webhooks later)
- No advanced pricing logic (just emissions + reporting)  
- No full automation of EU submission portal (out of scope)

Focus: **reliable embedded emissions + CBAM-ready reporting.**
