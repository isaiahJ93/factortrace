#!/usr/bin/env bash

set -euo pipefail



cd ~/Documents/Scope3Tool/backend



mkdir -p docs/api

mkdir -p .claude/commands



########################################

# 1) DECISIONS.md – Architecture Log

########################################

cat << 'EOF' > DECISIONS.md

# Architecture Decision Log – FactorTrace



This file captures non-trivial architecture decisions so we don't re-argue them in 3–6 months, and so agents/tools know which paths are intentional.



---



## 1. Multi-Tenant Isolation Strategy  

**Date:** 2024-11-30  

**Status:** Accepted



**Context**  

FactorTrace is a multi-tenant SaaS for Tier 1 & 2 suppliers and their buyers. We need strong, auditable tenant isolation without making schema management impossible.



**Decision**  

Use a single shared schema with:



- `tenant_id` column on all tenant-owned tables (emissions, vouchers, payments, reports, uploads, etc.).

- Application-layer enforcement:

  - All reads/writes must filter by `tenant_id == current_user.tenant_id`.

- Helper commands:

  - `/tenant-check` to detect missing filters.

- Optional DB-level hardening later (row-level security) but not for V1.



**Alternatives Considered**



1. Separate DB per tenant  

   - Pros: strong isolation.  

   - Cons: operational explosion, complex migrations, bad for thousands of suppliers.



2. Separate schema per tenant  

   - Pros: some isolation.  

   - Cons: same migration pain, harder to scale for small suppliers.



3. Postgres Row-Level Security (RLS) from day 1  

   - Pros: strong enforcement in DB.  

   - Cons: extra complexity and risk of misconfig at this stage; we want clear, inspectable query patterns first.



**Consequences**



- All code generation must respect `tenant_id` filters.

- Tests must include cross-tenant isolation cases.

- Later, we may add RLS for extra defence-in-depth, but the app-level pattern remains the same.



---



## 2. Number Format & CSV Handling  

**Date:** 2024-11-30  

**Status:** Accepted



**Context**  

Suppliers will upload CSVs from different locales: German-style `1.234,56` vs US/Intl `1,234.56`. Silent mis-parsing would destroy trust.



**Decision**



- Use a `sanitize_number()` helper (see `.claude/skills/csv-processing.md`) to:

  - Detect German vs US style by pattern.

  - Normalize to `1234.56` (dot decimal) before passing to Pint/pandas.

- All CSV ingestion must:

  - Read numeric fields as `str` then sanitize.

  - Return row/column-level errors, not a generic "bad CSV".



**Alternatives Considered**



1. Force users to pick a locale manually.  

   - More friction, slower flows.

2. Rely on pandas auto-parsing.  

   - Too risky; ambiguous cases slip through.



**Consequences**



- Slightly more complexity in the importer.

- Much higher safety and user trust.

- All future CSV logic must use the same sanitization strategy.



---



## 3. Emission Factor Architecture (DEFRA, EPA, EXIOBASE)  

**Date:** 2024-11-30  

**Status:** Accepted



**Context**  

FactorTrace must support multiple datasets (DEFRA, EPA, EXIOBASE, etc.) with consistent access patterns and metadata for auditability.



**Decision**



- Use a single `emission_factors` table with:

  - `dataset`, `scope`, `category`, `activity_type`

  - `country_code`, `year`

  - `factor`, `unit`

  - `metadata` JSON (source URL, notes, confidence, etc.)

- Access via service layer only (`app/services/emission_factors.py`).

- Implement waterfall lookup:

  1. Exact match (tenant + country + year).

  2. Country + closest year.

  3. Region/global fallback.



**Alternatives Considered**



- Separate tables per dataset.

- Fully denormalised factors per tenant.



**Consequences**



- Easier ETL from new datasets.

- Cleaner API for calculators.

- Must keep metadata complete for audit trails.



---



## 4. Authentication & Voucher-Based Access  

**Date:** 2024-11-30  

**Status:** Accepted



**Context**  

Tier 1 & 2 suppliers may not want full "account setup" friction just to generate a compliant report. We also need a way to sell credits.



**Decision**



- Use a voucher / credit-based model:

  - Buyers (or suppliers) purchase credit packs.

  - A voucher / access code is emailed.

  - Supplier can sign in using a code-based flow (plus basic details) to redeem and use credits.

- User auth stack:

  - JWT/session-backed auth after redeeming voucher.

  - All actions still tied to `tenant_id`.



**Alternatives Considered**



- Only email/password account model.

- Complex SSO from day one.



**Consequences**



- Faster onboarding for suppliers.

- Voucher/credit flows must be first-class in API and UI.

- Requires strong tracking of voucher status and abuse prevention.



---



## 5. Reporting Pipeline: PDF + XHTML/iXBRL  

**Date:** 2024-11-30  

**Status:** Accepted



**Context**  

FactorTrace must output human-readable PDFs and machine-readable XHTML/iXBRL aligned with ESRS/CSRD. These outputs may be large.



**Decision**



- Single canonical internal representation of results (structured dict / Pydantic model).

- Two main exporters:

  - PDF via templating engine (e.g. WeasyPrint).

  - XHTML/iXBRL via dedicated templates and tagging.

- No mixing PDF generation logic and calculation logic.



**Alternatives Considered**



- Generate PDF from XHTML (or vice versa) as primary path.

- Ad-hoc Jinja templates scattered around.



**Consequences**



- Clear seam for future regulators/standards.

- Easier to test/report differences.

- Performance budget must account for export time separately from calculation.



---



## 6. Scope of V1 Global Regulatory SaaS  

**Date:** 2024-11-30  

**Status:** Accepted



**Context**  

We aim at "V1 Global Regulatory SaaS", not a thin MVP, but also not all regimes at once.



**Decision**



- V1 focuses on:

  - CSRD/ESRS-compatible Scope 1–3 structure.

  - DEFRA/EPA/EXIOBASE (subset) factors.

  - Supplier-facing CSV importer + calculation + PDF + basic XHTML structure.

  - Voucher workflow for Tier 1 & 2 suppliers.

- Other regimes (CBAM, EUDR, FuelEU, etc.) are Phase 2+ and must not block V1.



**Consequences**



- All decisions should ask: "Does this make V1 better for Tier 1/2 suppliers?"

- Nice-to-have regulatory regimes must not derail core flows.



---



## 7. Future Decisions Placeholder



When making new decisions that affect architecture, performance, or compliance:



- Add a new section here.

- Reference the date, context, decision, alternatives, consequences.

EOF



echo "✅ DECISIONS.md created"



########################################

# 2) PERFORMANCE_BUDGET.md

########################################

cat << 'EOF' > PERFORMANCE_BUDGET.md

# Performance Budget – FactorTrace



These are non-negotiable performance targets that all code (including AI-generated) must respect, especially for CSV ingestion and reporting.



If a proposed approach is likely to violate these, it must be flagged and optimized.



---



## 1. API Response Times (Backend, p95)



- GET list endpoints (small datasets, e.g. reports list):  

  - Target: < 200ms

- GET single resource:  

  - Target: < 100ms

- POST/PUT/DELETE (standard CRUD):  

  - Target: < 300ms

- Heavy operations (kick off long-running jobs):  

  - Synchronous part: < 500ms (enqueue job, return 202 / job id).



---



## 2. CSV Import & Validation



Assume CSVs up to 50MB and 50k rows for suppliers.



- 1,000 rows:  

  - Target: < 2 seconds

- 10,000 rows:  

  - Target: < 10 seconds

- 50,000 rows:  

  - Target: < 60 seconds (with streaming + chunked validation)



Rules:



- Must stream / chunk large files, not load entire content into memory at once.

- Number sanitization + Pint validation must be vectorized where possible (avoid Python loops).

- Error reporting:

  - Row/column-level errors must still be captured without blowing up memory.



---



## 3. Emission Factor Lookups



For typical supplier workloads (hundreds to thousands of lookups per report):



- Single factor lookup (warm cache):  

  - Target: < 5ms per lookup.

- Bulk factor lookup (10k rows):  

  - Target: < 2 seconds using vectorized/optimized paths.



Rules:



- Use indexes on (`dataset`, `country_code`, `year`, `scope`, `category`).

- Prefer batched queries or in-memory maps over 10k individual DB round-trips.

- For hot paths, consider per-tenant caches (in-memory/Redis).



---



## 4. Reporting (PDF + XHTML/iXBRL)



For a typical supplier report:



- PDF generation:  

  - Target: < 5 seconds per report.

- XHTML/iXBRL generation:  

  - Target: < 8 seconds per report (more complex templates allowed).



Rules:



- Do heavy work in background jobs where needed.

- Avoid re-parsing large datasets per request; reuse cached factor data where possible.

- Ensure that exporting functions are pure / side-effect-free aside from logging.



---



## 5. Database Constraints



- No N+1 query patterns in high-traffic/list endpoints.

- Pagination mandatory for list endpoints:

  - Default page size: 25–50.

  - Max page size: 100.

- All foreign key and high-cardinality filter columns must be indexed:

  - `tenant_id`, `dataset`, `year`, `country_code`, `scope`, etc.



---



## 6. Memory Usage



- CSV processing (50MB file):  

  - Target peak memory: < 500MB.

- Standard API requests:  

  - Target per-request memory: < 50MB.



Rules:



- Avoid building huge in-memory Python lists/dicts if streaming is possible.

- Prefer generators / chunked processing where appropriate.



---



## 7. Frontend Performance (Target for V1)



- Initial dashboard load:  

  - Target: < 2 seconds on a typical EU connection.

- CSV upload UX:

  - Progress bar updates frequently; UI stays responsive.

- Bundle size:

  - Target: < 500KB gzipped for main app bundle.



---



## 8. How to Use This Budget



When generating or reviewing code:



1. Check new features against this budget.

2. If something is likely to break it:

   - Flag: "This approach may violate PERFORMANCE_BUDGET.md for X."

   - Propose alternative strategies (streaming, caching, batching, etc.).

3. For critical paths (CSV import, factor lookups, reporting):

   - Use `/perf-audit` to identify concrete bottlenecks.

EOF



echo "✅ PERFORMANCE_BUDGET.md created"



########################################

# 3) LEARNINGS.md

########################################

cat << 'EOF' > LEARNINGS.md

# Technical Learnings – FactorTrace



This is a living log of deep technical rabbit holes (Pint, EXIOBASE, XBRL, etc.).  

Each entry should be something you'd want Future You (or an agent) to reuse.



---



## 1. Pint & Fuel Density Contexts  

**Date:** 2024-11-30  

**Topic:** Converting volume (L) to mass (kg) for fuels



**What I learned**



- Pint cannot convert `L` → `kg` without a density context.

- For fuels like diesel, you must define a custom context (e.g. 0.835 kg/L).

- Contexts are opt-in and used with a `with ureg.context("name")` block.



**Code Pattern**



```python

import pint



ureg = pint.UnitRegistry()



diesel_context = pint.Context("diesel")

diesel_context.add_transformation("liter", "kilogram", lambda ureg, x: x * 0.835)

ureg.add_context(diesel_context)



with ureg.context("diesel"):

    mass = 100 * ureg.liter

    mass_kg = mass.to("kg")

Gotchas





Be explicit: different fuels have different densities.

Contexts must be documented (for audit) – include source of density values.

Do not silently assume densities without at least a comment and reference.







2. EXIOBASE / MRIO Basics



Date: 2024-11-30

Topic: Using EXIOBASE for spend-based factors



What I learned





EXIOBASE is a multi-regional input–output (MRIO) database, typically accessed via pymrio.

The raw files are huge (GB-level); you should not load them ad hoc in API requests.

Best practice is:



Pre-process into a smaller set of spend-based factors.

Populate emission_factors table with EXIOBASE-derived records.



Code Sketch



import pymrio



exio = pymrio.parse_exiobase3(path="IOT_2020_pxp.zip")

exio.calc_all()



# Example: satellite account / final demand emissions

factors = exio.satellite.F_Y

# Then aggregate & export to CSV → ETL into emission_factors

Gotchas





Country codes may not be pure ISO; mapping is required.

Some sectors might legitimately have zero emissions; filter carefully.

Pre-calculation can take minutes; keep this out of request paths.







3. XBRL / XHTML Template Strategy



Date: 2024-11-30

Topic: Generating compliant XHTML/iXBRL



What I learned





Best practice: keep a canonical internal model of report data and map that into templates.

Templates should:



Be versioned (e.g. ESRS_E1_v1).

Have explicit tag mappings (concept → line item).

Be validated via an XHTML/iXBRL validator before sending to users.



High-Level Pattern



def generate_xhtml(report_data: ReportModel) -> str:

    """

    Takes internal report model, renders XHTML/iXBRL.

    """

    context = build_xbrl_context(report_data)

    return render_template("esrs_e1.xhtml.jinja2", **context)

Gotchas





Small mistakes in tags/contexts can invalidate the whole document.

Keep a tiny, known-good sample file for regression tests.







4. [Next Learning Here]



When you go deep on something (e.g. new regime, new library, non-trivial bug):





Add a new section: Topic, What I learned, Code pattern, Gotchas.

Reference relevant files (ETL scripts, services, tests).

EOF



echo "✅ LEARNINGS.md created"


########################################







# 4) API Contracts – docs/api/*.md



########################################



cat << 'EOF' > docs/api/emissions-contract.md





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

EOF



echo "✅ docs/api/emissions-contract.md created"



cat << 'EOF' > docs/api/voucher-purchase-contract.md







Voucher/Credit Purchase API Contract



Contract-first spec for purchasing and redeeming vouchers/credits.









POST /api/v1/vouchers/purchase



Purpose

Allow a buyer (or supplier) to purchase a pack of credits/vouchers.



Request Body (JSON)



Required:





pack_type (string): e.g. "SINGLE_REPORT", "BUNDLE_10", "BUNDLE_50".

quantity (int): Number of vouchers in this purchase (for bulk packs).

buyer_email (string): Email to send voucher codes to.

currency (string): ISO 4217 (e.g. "EUR").

payment_reference (string): Reference from payment provider (Stripe, etc.).



Optional:





buyer_name (string)

notes (string)



Business Rules





Price must be calculated server-side based on pack_type, quantity, and current pricing model.

tenant_id is derived from the authenticated buyer’s organisation.

One or more voucher codes are generated and persisted with:



code (secure random string).

tenant_id.

status = "UNUSED".

credits (e.g. number of reports allowed).

Email(s) must be queued/sent with voucher codes to buyer_email.



Success Response (201)



{

  "purchase_id": "uuid",

  "tenant_id": "tenant_abc",

  "pack_type": "BUNDLE_10",

  "quantity": 10,

  "currency": "EUR",

  "total_amount": 9500,

  "vouchers": [

    {

      "code": "FT-ABC123-XYZ",

      "status": "UNUSED",

      "credits": 1

    }

  ],

  "created_at": "2024-11-30T10:00:00Z"

}







POST /api/v1/vouchers/redeem



Purpose

Allow a supplier to redeem a voucher code to gain access to FactorTrace (credits/reports).



Request Body (JSON)



Required:





code (string): Voucher code received via email.

email (string): Supplier contact email.

company_name (string): Supplier organisation.



Optional:





name (string): Contact person name.



Business Rules





Find voucher by code:



If not found → 404.

If already used / expired → 400 with clear error.

Link voucher to a supplier tenant:



If tenant exists for this company → link.

Else create a new tenant (Tier 1/2 supplier) and link voucher.

Mark voucher as:



status = "USED".

Store redeemed_at, redeemed_by_email.

Issue auth credentials / session for supplier so they can:



Upload data.

Use credits to generate reports.



Success Response (200)



{

  "tenant_id": "tenant_supplier_123",

  "voucher_code": "FT-ABC123-XYZ",

  "credits_remaining": 1,

  "access_token": "jwt-or-session-token",

  "consumed": true

}

Error Responses



400 Bad Request:



{

  "detail": [

    {

      "field": "code",

      "message": "Voucher has already been used or is expired."

    }

  ]

}

404 Not Found – unknown voucher code.









GET /api/v1/vouchers



Purpose

List vouchers for the current tenant (buyers).



Business Rules





Tenant-scoped.

Paginated.

No exposure of voucher codes from other tenants.







Tests Required



Successful purchase flow (vouchers created, email queued).

Successful redeem flow (voucher → tenant link, status change).

Double redeem attempt fails with 400.

Cross-tenant voucher access blocked.

Edge cases: invalid code, expired code, wrong email (if enforced).

EOF



echo "✅ docs/api/voucher-purchase-contract.md created"



########################################







# 5) /review command



########################################

cat << 'EOF' > .claude/commands/review.md







/review



Comprehensive code review helper for FactorTrace.



When I run this command on one or more files (for example:

/review app/api/v1/emissions.py app/services/emissions_service.py):









1. Security



Check for:





Missing tenant_id filters on any tenant-owned data (emissions, vouchers, payments, reports, uploads).

Direct DB access from route handlers that bypasses service layer patterns described in CLAUDE.md.

Unvalidated user input:



Path/query/body values used directly in DB queries.

Unsanitized CSV data passed straight into Pint/pandas.

Authentication/authorization gaps:



Endpoints that should require auth but do not.

Actions not checked against current tenant / user permissions.



Output:





🚨 Critical security issues with:



File + line references.

Concrete patch suggestions.







2. Performance



Check for:





N+1 query patterns (loops doing DB queries repeatedly).

Missing indexes on hot filter columns (e.g. tenant_id, dataset, year, country_code).

Inefficient pandas usage (row-wise apply for huge data, unnecessary copies).

Loading entire large files or tables into memory when streaming/chunking is needed.



Use PERFORMANCE_BUDGET.md as the baseline and flag any likely violations.



Output:





⚠️ Performance warnings with:



Why it is a problem.

Suggested refactors or patterns (chunking, caching, batching).







3. Code Quality & Maintainability



Check for:





Missing type hints on public functions / methods.

Inconsistent naming or confusing abstractions.

Missing or weak error handling (especially around I/O, CSV, external services).

Duplicated logic that could be moved to a helper/service.



Output:





💡 Suggestions for improving clarity, structure, and reuse.







4. Testing & Coverage



Check for:





Missing tests for new branches / edge cases.

No negative tests (invalid input, cross-tenant attempts, malformed CSV).

Gaps in integration tests (e2e flows: upload → calculate → report).

For critical paths, ensure tests align with contracts in docs/api/*.md.



Output:





Test checklist:



Which tests exist.

Which tests are missing and should be added.







5. Regulatory & Domain Alignment



Given FactorTrace is a Global Regulatory SaaS, also check:





Alignment with decisions in DECISIONS.md (do not contradict architecture choices without explanation).

Proper use of units, factors, and datasets:



No magic constants where a factor lookup is expected.

Logging & auditability for key actions (calculations, report generation, voucher redemption).







Output Format



Return a structured review:





🚨 Critical (must fix before merge)

⚠️ Warnings (should fix soon)

💡 Suggestions (nice to have)

✅ What’s good (patterns worth repeating)



Where possible, include:





File + line numbers.

Example patches (diff-style) for high-impact fixes.

EOF



echo "✅ .claude/commands/review.md created"



########################################







# 6) /ship-check command



########################################

cat << 'EOF' > .claude/commands/ship-check.md







/ship-check



Pre-deployment quality gate for FactorTrace.



When I run this command, walk through all sections and report ✅ / ❌ with details.









1. Security ✓



Run /tenant-check on all relevant backend files (API routes, services, models).

Confirm all tenant-owned tables use tenant_id and are always filtered by it.

Validate all user input via Pydantic schemas (no raw dicts).

Ensure no hardcoded secrets (use env vars; .env.example present).

Check CORS settings are appropriate for the deployed frontend.

Confirm voucher flows cannot be abused (double redeem, guessing codes).







2. Testing ✓



All tests passing: pytest -v.

Coverage above agreed threshold (e.g. > 80% for core modules).

Security tests:



Cross-tenant access attempts blocked for emissions, vouchers, payments, reports.

E2E tests for:



CSV upload → validate → import → calculate → generate report.

Voucher purchase → email stub/queue → redeem → access flow.

Regression tests exist for previously fixed critical bugs.







3. Performance ✓



Use /perf-audit and manual reasoning based on PERFORMANCE_BUDGET.md.





CSV importer meets: 10k rows in < 10s.

Factor lookups are batched/cached, no obvious N+1.

Reporting (PDF/XHTML) within budget for typical report size.

DB indexes in place for hot filters:



tenant_id, dataset, year, country_code, etc.

Flag any risks and propose concrete mitigation steps if something is marginal.







4. Data & Regulatory Integrity ✓



Emission factor datasets (DEFRA/EPA/EXIOBASE subset) correctly loaded with:



Dataset name, year, country, scope, category, unit, factor.

Unit conversions:



Pint contexts for fuels/energy are correct and documented.

Currency handling:



FX normalization rules are clear and deterministic where used.

Reports align with:



ESRS-style structure (Scope 1/2/3 breakdown).

Internal decisions in DECISIONS.md.







5. Documentation ✓



README.md describes:



How to run locally.

How to run tests.

How to run migrations.

docs/api/*.md contracts match actual behaviour (or are updated).

DECISIONS.md contains latest major architecture choices.

LEARNINGS.md updated with any big rabbit-hole learnings.

Environment variables documented (e.g. ENV, DB URL, mail provider, factor paths).







6. Deployment & Ops ✓



Docker image builds successfully.

docker-compose / infra config runs everything locally.

Alembic migrations up to date and tested on a clean DB.

Health check endpoint (/health or similar) implemented and returns status.

Basic logging:



Errors, warnings, key business events (voucher redeemed, report generated).



Optional but ideal:





Monitoring/alerts planned (even if minimal at first).

Log retention strategy thought through (especially for audit trails).







7. Final Decision



After evaluating all sections, provide:



Summary:





✅ Ready to ship to staging/production

or

❌ Not ready, with blocking issues listed.



Suggested next steps:





List of highest-priority fixes before deployment.



This command should act as a pre-flight checklist before exposing FactorTrace to real Tier 1 and Tier 2 suppliers.

EOF



echo "✅ .claude/commands/ship-check.md created"



echo ""

echo "=========================================="

echo "All FactorTrace meta markdown files created/updated."

echo "=========================================="


