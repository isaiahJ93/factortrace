# FactorTrace Roadmap  
Multi-Regime Compliance Layer for Tier 1 & 2 Suppliers

**Owner:** Isaiah  
**Last updated:** December 2025  
**Status:** CSRD/ESRS core in build; multi-regime expansion planned

---

## 1. Vision

FactorTrace is a **multi-regime regulatory compliance layer** for **Tier 1 & Tier 2 suppliers** in global value chains, with:

- **Suppliers** as primary users (CSRD/ESRS, CBAM, EUDR, ISSB outputs)
- **Enterprise OEMs / buyers** as economic buyers (voucher bundles, API access)
- **Consultants / platforms** as distribution partners (white-label + API)

Long-term positioning:

> “FactorTrace is the embedded compliance engine for supply chains – suppliers plug in once and receive **multi-regime audit-grade outputs** across CSRD/ESRS, CBAM, EUDR, ISSB and future regimes.”

The roadmap below defines how we get from **CSRD/ESRS V1** → **multi-regime global layer** in **phased, shippable increments**.

---

## 2. Guiding Principles

These apply to every phase and every regime:

1. **Supplier-First Design**
   - Minimize data entry friction.
   - Reuse activity/spend data across regimes.
   - Offer clear, human-readable explanations next to any score or metric.

2. **Regime-Agnostic Core, Regime-Specific Shells**
   - Single **core data model**: activities, spend, products, locations, suppliers, buyers.
   - Regime modules (CSRD/ESRS, CBAM, EUDR, ISSB) are **thin layers**:
     - Mapping tables
     - Calculation rules
     - Reporting templates

3. **Voucher & API-First Monetization**
   - OEMs buy **vouchers / credits** in bulk.
   - Suppliers redeem vouchers to generate **reports**.
   - Consultants / platforms use **API + white-label UI**.

4. **Audit-Grade Output by Default**
   - XHTML/iXBRL + PDF.
   - Full lineage: inputs → factors → calculations → outputs.
   - Logs, hashes, and change history ready for audit.

5. **AI-Accelerated, Not AI-Opaque**
   - Claude Agentic Coder used to build and refactor.
   - All regime logic remains **transparent** in code and docs.
   - `.md` specs are the **source of truth**.

---

## 3. Roadmap Overview

Timeframes are approximate and represent **build focus**, not exclusivity. Outreach and infra run in parallel.

### Phase 0 — Foundation (In Progress / 2025 Q4–2026 Q1)

**Goal:** Solid CSRD/ESRS backbone + AI-friendly meta + basic GTM.

Core outputs:

- CSRD/ESRS Scope 1–3 engine:
  - Activity-based (DEFRA/EPA)
  - Spend-based (EXIOBASE)
  - Supplier-level emissions & category breakdowns
- Reporting pipeline:
  - PDF + XHTML/iXBRL export (ESRS-aligned)
- AI meta system:
  - `CLAUDE.md`, `plan.md`, `DECISIONS.md`, `PERFORMANCE_BUDGET.md`, `LEARNINGS.md`
  - `.claude/skills/*` and `.claude/commands/*`
  - `docs/api/emissions-contract.md`, `docs/api/voucher-purchase-contract.md`
- Minimal UI:
  - Supplier dashboard for emissions input and report download
- Outreach prep:
  - Cold email infra warming
  - Initial pitch for Tier 1/2 suppliers + pilot OEMs

**Exit criteria:**

- A Tier 1 supplier can:
  - Upload activity/spend data.
  - See Scope 1–3 results.
  - Download an ESRS-aligned PDF/XHTML report.
- Claude can reliably:
  - Generate/rewrite code within the current architecture.
  - Extend endpoints without breaking multi-tenant isolation.
- Repo is **investor-ready** (docs, tests, architecture).

---

### Phase 1 — CSRD/ESRS Product Hardening (2026 H1)

**Goal:** Turn CSRD/ESRS into a **sellable, repeatable V1** for Tier 1/2 suppliers.

Tracks:

1. **Product & UX**
   - Smooth CSV import with:
     - Locale handling (comma vs dot decimals).
     - Templates by sector.
   - Guided workflows:
     - “Tell us about your business” → pre-configured categories.
   - Basic multi-tenant client management (for OEM/consultant).

2. **Architecture & Reliability**
   - Apply performance budget from `PERFORMANCE_BUDGET.md`:
     - P95 latency targets.
     - Import size limits and streaming behavior.
   - Strengthen tenant isolation:
     - Add automated checks & tests for tenant leaks.
   - Expand test coverage:
     - GHG Protocol alignment tests.
     - Golden path integration tests for 3–5 example suppliers.

3. **Reports & Evidence**
   - Harden XHTML/iXBRL output:
     - ESRS tags verified against regulator samples where possible.
   - Add “Evidence Pack” bundle:
     - CSV input snapshot.
     - Factor tables used.
     - Calculation logs (optional).

4. **Commercial & GTM**
   - Launch **voucher-based pricing**:
     - Single report, bundle of 10, bundle of 50.
   - Pilot programs:
     - Target 3–5 Tier 1/2 suppliers and 1 OEM willing to sponsor vouchers.
   - Build simple partner console:
     - Consultants manage their client suppliers.

**Exit criteria:**

- 5–10 real or “live-like” suppliers successfully onboarded.
- Reports validated by at least one external advisor or pseudo-auditor.
- System stable under realistic data volumes.

---

### Phase 2 — CBAM Module (2026 H1–H2)

**Goal:** Add CBAM as the second full regime, using the shared core.

CBAM requirements (high level):

- Product-level embedded emissions for covered goods
- CN codes / product taxonomy mapping
- Import declaration outputs (aligned with CBAM reporting)
- Ability to reuse:
  - Activity data (energy, process emissions)
  - Spend data
  - Supplier identifiers

**Key workstreams:**

1. **Data Model Extensions**
   - Add product & trade data entities:
     - `cbam_product`, `cn_code`, `import_shipment`, `border_point`.
   - Link to existing:
     - Supplier, buyer, activity, spend.

2. **Mapping & Factors**
   - Create EXIOBASE/sector ↔ CN code mapping tables.
   - Ingest CBAM default emission factors where applicable.
   - New mapping YAMLs: `data/mappings/cbam_*`.

3. **Calculation Engine**
   - Implement CBAM calculation service:
     - Per product embedded emissions.
     - Allocation between direct emissions, electricity, upstream.
   - Expose via API:
     - `/cbam/calculate`
     - `/cbam/report-preview`

4. **Reporting**
   - Define format in `docs/regimes/cbam.md`.
   - Implement:
     - CBAM summary report (PDF).
     - CBAM declaration export (machine-readable structure).

5. **Productization**
   - UI flows:
     - “Import customs data / product list.”
     - Map to factors, validate, preview charges.
   - Commercial:
     - CBAM add-on credits.
     - Bundled pricing for OEMs importing from many suppliers.

**Exit criteria:**

- At least one realistic CBAM scenario flows end-to-end:
  CSV customs data → FactorTrace → CBAM report + declaration export.
- Core CSRD/ESRS flows remain unchanged and stable.
- Claude can extend CBAM logic using `docs/regimes/cbam.md` as authority.

---

### Phase 3 — EUDR Module (2026 H2–2027 H1)

**Goal:** Add EUDR deforestation compliance for commodity-linked suppliers.

EUDR requirements (high level):

- Commodity tracking (soy, palm oil, timber, cattle, cocoa, coffee, rubber)
- Geo-linked plots / origins
- Deforestation risk and due diligence statements
- Supply chain path (origin → processor → trader → buyer)

**Key workstreams:**

1. **Supply Chain & Geo Modeling**
   - New entities:
     - `commodity`, `plot`, `geo_location`, `supply_chain_link`.
   - Graph-like relationships to capture multi-step supply chains.
   - Store deforestation risk scores per plot/region.

2. **Risk & Due Diligence Logic**
   - Implement risk scoring engine described in `docs/regimes/eudr.md`:
     - Combine geo risk (public datasets) + supplier behavior + volume.
   - Generate:
     - Due diligence statements.
     - Risk mitigation actions.

3. **Integrations (Phase 3a = stubs, Phase 3b = real)**
   - Phase 3a:
     - Design connectors and mock responses for forest/land-use APIs.
   - Phase 3b:
     - Implement real integrations (e.g., Global Forest Watch or equivalent).

4. **Reporting & UI**
   - EUDR report template:
     - Supplier-level view.
     - Commodity/plot-level view.
   - UI assistance:
     - “Explain my EUDR score.”
     - “What should I do to reduce risk?”

5. **Commercial & Target Segment**
   - Focus first on:
     - Food & agri suppliers.
     - Timber and biomass operators.
   - Build EUDR-specific voucher tiers.

**Exit criteria:**

- A commodity supplier can:
  - Define their supply chain for key commodities.
  - Receive an EUDR risk assessment + due diligence statement.
- EUDR module reuses:
  - Core supplier model.
  - Voucher / API monetization model.

---

### Phase 4 — ISSB Climate Module (2027 H1–H2)

**Goal:** Layer **financial materiality + climate risk** on top of emissions data, targeting CFO / investor use cases.

ISSB requirements (high level):

- Climate-related risks & opportunities
- Financial materiality (linking emissions & transition to revenue, EBITDA, etc.)
- Scenario analysis (1.5°C, 2°C, 3°C)
- Transition plans and targets

**Key workstreams:**

1. **Financial Data Model**
   - New entities:
     - `financial_statement`, `segment`, `risk_exposure`.
   - Link emissions outputs to:
     - Revenue streams.
     - Cost categories.
     - Capital expenditure (where applicable).

2. **Materiality & Risk Engine**
   - Implement logic defined in `docs/regimes/issb.md`:
     - Map emissions + sector to climate risk categories.
     - Estimate order-of-magnitude financial impacts.
   - Outputs:
     - Risk heatmap.
     - Top 5 financial exposures with explanations.

3. **Scenario Analysis**
   - Start with deterministic scenarios:
     - Stress tests rather than full stochastic models.
   - Use existing emissions data for:
     - Carbon cost sensitivities (e.g., price per tCO₂e).
     - Revenue at risk for high-exposure segments.

4. **Reporting**
   - ISSB climate disclosure pack:
     - Narrative sections + structured tables.
   - Integration path:
     - Export structured data for external financial reporting tools.

5. **Target Users & GTM**
   - CFO-adjacent:
     - Sustainability teams working with finance.
   - Offer ISSB as an **add-on module** for:
     - Large suppliers.
     - OEMs wanting harmonized supplier data.

**Exit criteria:**

- At least one synthetic case produces:
  - Emissions inputs → ISSB climate risk view → scenario outputs.
- CFO-friendly summary (high-level) + data download (detailed) available.

---

## 4. Horizontal Tracks (Run Across All Phases)

These are ongoing streams that support the whole roadmap:

### A. AI & Developer Experience

- Keep Claude meta current:
  - Update `DECISIONS.md` after major architectural changes.
  - Extend `LEARNINGS.md` with EUDR/CBAM/ISSB insights.
  - Add regime-specific `.claude/skills` if needed.
- Add commands as you grow:
  - `/cbam-test`
  - `/eudr-model-check`
  - `/issb-sanity-check`
- Maintain `.claudeignore` as repo grows to avoid context bloat.

### B. Security & Compliance

- Strengthen multi-tenancy:
  - Fuzz tests for cross-tenant leaks.
  - Centralized tenant isolation middleware.
- Add role-based access:
  - Supplier vs OEM vs Consultant roles.
- Logging & audit trails:
  - Per regime, with clearly tagged entries.

### C. Performance & Scalability

- Enforce `PERFORMANCE_BUDGET.md` on:
  - Large CSV imports.
  - Bulk calculations (CBAM shipments, EUDR supply chains).
  - ISSB scenario runs.
- Add background jobs / task queues for:
  - Heavy reports.
  - Large data imports.

### D. GTM & Market Learning

- Run continuous outreach:
  - Emails to Tier 1/2 suppliers.
  - Conversations with OEMs about voucher programs.
- Use pilots to refine:
  - UX.
  - Pricing.
  - Regime prioritization.

---

## 5. Milestone Targets (Subject to Change)

Very rough, ambition-aligned checkpoints:

- **2026 H1**
  - CSRD/ESRS V1 stable and in pilot with real suppliers.
  - CBAM design finished and partially implemented.
- **2026 H2**
  - CBAM module live for at least one sector.
  - First OEM / buyer using vouchers at small scale.
- **2027 H1**
  - EUDR module live for at least one commodity vertical.
  - End-to-end: Supplier → Multi-regime outputs via one platform.
- **2027 H2**
  - ISSB climate module functional for pilot customers.
  - FactorTrace recognized as **multi-regime supply-chain compliance engine**, not just an ESG tool.

---

## 6. What Claude Agentic Coder Should Do with This

When using Claude Agentic Coder in this repo, this roadmap should be treated as:

- **North Star for architecture decisions**
  - Prefer generic, extensible patterns that support additional regimes.
  - Keep regime-specific logic isolated and documented.
- **Planning reference**
  - When asked to implement something “next,” prefer tasks that unlock Phase 0/1/2 goals first.
- **Context for refactors**
  - When refactoring, keep in mind:
    - Multi-regime extensions.
    - Supplier-first UX.
    - Voucher/API model.

If a change conflicts with this roadmap, Claude should **flag it** in the explanation and suggest an alternative that preserves the multi-regime vision.

---

## 7. Risks & Focus

Key risks:

- Over-scope (trying to fully perfect all regimes simultaneously).
- Regulatory drift (rules evolve; must keep docs and logic aligned).
- Complexity creep (EUDR/ISSB models getting too complex to maintain).

Mitigation:

- Always ship **thin vertical slices**:
  - One sector, one commodity, one scenario at a time.
- Keep `.md` specs (CSRD, CBAM, EUDR, ISSB) as the **single source of truth**.
- Use tests + golden paths for each regime as regression anchors.

---

**Summary:**  
FactorTrace is not “just” a CSRD tool. This roadmap makes it a **multi-regime compliance layer for supply chains**: suppliers integrate once, and over time gain CSRD, CBAM, EUDR, and ISSB coverage from the same core engine. This document tells both humans and AI *what to build next* and *how all the pieces fit together*.
