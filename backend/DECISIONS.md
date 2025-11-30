
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

