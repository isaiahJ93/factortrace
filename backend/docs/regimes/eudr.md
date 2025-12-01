# EUDR Regime Specification – FactorTrace

Status: Draft → Target V1 ready in 6–9 weeks  
Owner: Isaiah + Claude Agentic Coder  
Primary Users: EU operators/traders dealing with EUDR commodities, Tier 1–2 suppliers, OEMs, traders, brokers  

---

## 1. What EUDR Is (Working Model for the System)

EUDR = **EU Deforestation Regulation**.  
We care about it as a **commodity + geography + supply-chain + risk assessment** problem.

**Internal mental model for FactorTrace:**

> “For a given operator/trader, and for a given set of EUDR commodities, we must prove that goods placed on the EU market are deforestation-free and legally produced, by linking each batch/lot to geolocated plots and running a risk assessment.”

We don’t need to implement every nuance of the law. We need a **productised core** that:

1. Tracks **commodities, batches, and geolocations**  
2. Links them into a **supply chain graph** (origin → intermediaries → EU operator)  
3. Pulls **geospatial risk signals** (deforestation alerts, protection status, etc.)  
4. Runs a **due diligence risk scoring model**  
5. Produces an **EUDR due diligence statement / report** that can be attached to official submissions and customer audits.

---

## 2. Supported Scope in V1

### 2.1 Commodities

Start with the official EUDR list, but focus V1 on a few:

Core V1 commodities (realistic wedge):

- Cattle (beef/leather)
- Cocoa
- Coffee
- Palm oil
- Soy
- Timber
- Rubber

We model commodities generically so adding more is just adding rows, not schema changes.

### 2.2 Geographic Coverage

- Global, but risk data likely richer for:
  - LATAM (Brazil, Colombia, etc.)
  - Southeast Asia (Indonesia, Malaysia, etc.)
  - Central & West Africa

We assume access to one or more geospatial sources later (e.g. Global Forest Watch, national datasets).

---

## 3. Data Model Additions

We extend FactorTrace with **supply-chain & geospatial entities**.

### 3.1 Core New Tables

1. **eudr_commodity**
   - `id`
   - `name` (e.g. “coffee”, “cocoa”, “palm_oil”)
   - `hs_code` (nullable – HS/CN mapping)
   - `description`
   - `risk_profile_default` (low/medium/high – coarse default)

2. **eudr_operator**
   - `id`
   - `tenant_id` (FK → tenant; represents the EU operator/trader side)
   - `name`
   - `role` (`operator` / `trader` / `supplier`)
   - `country` (ISO)
   - `identifier` (e.g. VAT/registration ID)

3. **eudr_supply_site**
   - `id`
   - `operator_id` (FK → eudr_operator – the entity controlling the site)
   - `commodity_id` (FK → eudr_commodity)
   - `name`
   - `country`
   - `geometry` (WKT / GeoJSON stored as text or PostGIS later)
   - `lat`, `lon` (numeric; centroid)
   - `area_ha` (numeric)
   - `legal_title_reference` (string – deed/registry reference)

4. **eudr_batch**
   - `id`
   - `batch_reference` (string – provided by user)
   - `commodity_id` (FK → eudr_commodity)
   - `volume` (numeric)
   - `volume_unit` (e.g. tonnes, m³, kg, bags)
   - `harvest_year` (int)
   - `origin_site_id` (FK → eudr_supply_site)
   - `origin_country`
   - `created_at`, `updated_at`

5. **eudr_supply_chain_link**
   - `id`
   - `from_batch_id` (FK → eudr_batch)
   - `to_batch_id` (FK → eudr_batch)
   - `from_operator_id` (FK → eudr_operator)
   - `to_operator_id` (FK → eudr_operator)
   - `link_type` (`purchase`, `processing`, `mixing`, `transport`, `aggregation`)
   - `documentation_reference` (string – invoice/contracts, optional)
   - `created_at`

This forms a **graph** (batches as nodes, links as edges).

6. **eudr_georisk_snapshot**
   - `id`
   - `supply_site_id` (FK → eudr_supply_site)
   - `source` (e.g. `GFW`, `NATIONAL_CADASTRE`)
   - `snapshot_date`
   - `deforestation_flag` (bool)
   - `tree_cover_loss_ha` (numeric)
   - `protected_area_overlap` (bool)
   - `risk_score_raw` (0–100)
   - `risk_level` (`low`, `medium`, `high`)
   - `details_json` (JSONB/text – extended geo info)

7. **eudr_due_diligence**
   - `id`
   - `tenant_id` (FK → tenant)
   - `operator_id` (FK → eudr_operator – typically EU operator)
   - `reference` (string – user-facing DD statement id)
   - `commodity_id`
   - `period_start`, `period_end`
   - `status` (`draft`, `final`, `archived`)
   - `overall_risk_level` (`low`, `medium`, `high`)
   - `overall_risk_score` (0–100)
   - `justification_summary` (text)
   - `created_at`, `updated_at`

8. **eudr_due_diligence_batch_link**
   - `id`
   - `due_diligence_id` (FK → eudr_due_diligence)
   - `batch_id` (FK → eudr_batch)
   - `batch_risk_score`
   - `batch_risk_level`
   - `included_volume` (numeric)
   - `included_volume_unit`

### 3.2 Reuse Existing Tables/Concepts

We **reuse**:

- Tenant model & multi-tenancy decision from `DECISIONS.md`
- Existing reporting/export infra (XHTML/PDF)
- Voucher model later (OEM/retailers funding due diligence for suppliers)

---

## 4. Geospatial & Risk Inputs

We don’t bake in a specific provider now. We design for pluggability.

### 4.1 Geospatial Risk Provider Abstraction

Create a simple internal abstraction:

- `eudr_georisk_provider` (Python service, not DB table):

Methods:

- `get_site_risk(supply_site: EudrSupplySite) -> EudrGeoriskSnapshot`
  - Input: `lat`, `lon`, `geometry`, `commodity`, `harvest_year`
  - Output: filled `eudr_georisk_snapshot` row (or DTO)

Implementation V1:

- Can be:
  - Mock / static risk (for dev & early pilots)
  - Simple spreadsheets with region-based risk
  - Later: actual external APIs (GFW, etc.)

Claude should design this so:

- It’s easy to mock in tests
- It can be replaced later with real API integrations without rewriting the rest of the EUDR logic

---

## 5. Risk Scoring Model (V1)

We don’t build a full research-grade risk model. We build a **transparent, configurable scoring system**.

### 5.1 Inputs Per Batch

For a given `eudr_batch`:

- Commodity risk baseline (from `eudr_commodity.risk_profile_default`)
- Geospatial risk:
  - `deforestation_flag`
  - `tree_cover_loss_ha`
  - `protected_area_overlap`
  - `source` and `snapshot_date`
- Supply chain complexity:
  - Number of hops in `eudr_supply_chain_link` from origin site to EU operator
  - Number of jurisdictions involved
- Documentation strength:
  - Presence/absence of:
    - contracts
    - certificates
    - traceability docs (optional in V1 as boolean flags)

### 5.2 Build a Simple Weighted Model

Define a first-pass model (configurable later):

Example:

- Start with `score = 0`
- Commodity baseline:
  - low → +10
  - medium → +25
  - high → +40
- Geospatial:
  - `deforestation_flag == True` → +40
  - `protected_area_overlap == True` → +30
  - `tree_cover_loss_ha > threshold` → +20
- Supply chain:
  - each hop beyond 2 → +5 (cap at some max)
  - each additional country beyond 1 → +5
- Documentation:
  - missing key documentation → +10–20

Then clamp `score` to 0–100 and map:

- 0–30 → `low`
- 31–60 → `medium`
- 61–100 → `high`

Claude should implement:

- A dedicated module, e.g. `app/services/eudr_risk.py`
- Use Pydantic models to pass structured inputs around
- Make weights & thresholds constants so we can tweak them later

---

## 6. API Design for EUDR

Base path:

- `/api/v1/eudr/`

### 6.1 Entities

Endpoints (contract-first; Claude should generate Pydantic + OpenAPI):

1. **Commodities**

   - `GET /eudr/commodities/`
     - List existing commodities, filter by `name` or `hs_code`
   - `POST /eudr/commodities/`
     - Admin use; not necessarily exposed to all tenants in V1

2. **Operators**

   - `POST /eudr/operators/`
     - Create operator (usually the tenant’s own entity + key suppliers)
   - `GET /eudr/operators/`
     - List operators for tenant

3. **Supply Sites**

   - `POST /eudr/supply-sites/`
     - `operator_id`, `commodity_id`, `country`, `lat`, `lon`, optional `geometry`, `area_ha`
   - `GET /eudr/supply-sites/{id}`
   - `GET /eudr/supply-sites/`
     - Filter by operator, commodity, country

4. **Batches**

   - `POST /eudr/batches/`
     - `batch_reference`, `commodity_id`, `volume`, `volume_unit`, `harvest_year`, `origin_site_id`
   - `GET /eudr/batches/{id}`
   - `GET /eudr/batches/`
     - Filter by commodity, site, operator, harvest year

5. **Supply Chain Links**

   - `POST /eudr/supply-chain-links/`
     - `from_batch_id`, `to_batch_id`, `from_operator_id`, `to_operator_id`, `link_type`, documentation reference
   - `GET /eudr/supply-chain-links/`
     - Filter by batch, operator

6. **Risk & Due Diligence**

   - `POST /eudr/due-diligence/`
     - Create a due diligence record for:
       - `operator_id`, `commodity_id`, `period_start`, `period_end`, list of `batch_ids`
   - `POST /eudr/due-diligence/{id}/evaluate`
     - Trigger risk evaluation:
       - Compute per-batch risk
       - Aggregate to overall risk & fill `eudr_due_diligence` fields
   - `GET /eudr/due-diligence/{id}`
   - `GET /eudr/due-diligence/`
     - Filter by status, commodity, period

7. **Georisk Snapshots**

   - `POST /eudr/supply-sites/{id}/refresh-risk`
     - Call the **georisk provider** → create `eudr_georisk_snapshot`
   - `GET /eudr/supply-sites/{id}/risk`
     - Fetch latest or historical risk data

All endpoints:

- Must be **tenant-scoped** per `DECISIONS.md`
- No cross-tenant leakage

---

## 7. EUDR Report Template

We reuse report infrastructure (Jinja2 + XHTML/iXBRL export) and define an **EUDR due diligence report**.

### 7.1 Core Sections

1. **Header**
   - Operator name, country, identifiers
   - Period covered
   - Commodity (or commodities)

2. **Summary**
   - Number of batches
   - Total volume covered
   - Overall risk level & score
   - Breakdown of risk levels (how many low/medium/high batches)

3. **Geospatial & Risk Overview**
   - Map/summary of origin countries/regions (V1 textual)
   - Count of:
     - sites with deforestation flags
     - protected area overlaps
   - Risk score distribution

4. **Supply Chain**
   - Description of supply chain complexity:
     - average number of hops
     - number of jurisdictions

5. **Risk Mitigation & Justification**
   - For `medium/high` risk:
     - include textual justification from `justification_summary`
     - list of mitigation steps (optional fields later)

6. **Annex – Batch-Level Table**
   For each batch:
   - `batch_reference`
   - `commodity`
   - `origin_country`
   - `origin_site_id`
   - `volume`, `volume_unit`
   - `batch_risk_level`, `batch_risk_score`

### 7.2 Output Types

- PDF (for customers/audits)
- XHTML/iXBRL (for digital filing/archives)
- CSV/XLSX (for further analysis by customers or auditors)

Claude should:

- Create a dedicated EUDR template file (e.g. `templates/eudr_due_diligence.html` / `.xhtml`)
- Use same export pipeline patterns as ESRS reports

---

## 8. Validation & Edge Cases

Claude must add tests that cover:

1. **Site missing georisk data**
   - Ensure DD evaluation either:
     - uses fallback risk; or
     - marks as “missing georisk” in report
   - Make behavior explicit in code & LEARNINGS.md if needed

2. **Circular supply chain links**
   - Detect and prevent infinite loops in graph traversal

3. **Mixed commodities**
   - DD statements with multiple commodities:
     - For V1 we can:
       - either restrict to single commodity per DD; or
       - handle multi-commodity but clearly segment in report
   - Decide and document in code comments + DECISIONS.md

4. **Large graph**
   - Many batches / links (e.g. 10k+)
   - Ensure we respect `PERFORMANCE_BUDGET.md`:
     - limit queries
     - use efficient graph traversal (no N+1 loops in Python)

5. **Geospatial precision**
   - Handle cases where only centroid provided vs full polygon
   - Accept lat/lon only for V1 and store geometry later

---

## 9. UX / Workflow Expectations

We don’t need full UI spec, but Claude should assume:

- **EUDR section in frontend** with:
  - Commodity overview
  - Supply sites map/list
  - Batches and traceability links
  - Due Diligence “wizard”

High-level workflows:

1. **Data onboarding flow**
   - Upload CSV of:
     - sites (lat/lon, commodity, operator)
     - batches (batch_id, commodity, site, volume, year)
   - Optional CSV for supply chain links

2. **Risk refresh flow**
   - Button: “Refresh geospatial risk” (per site or bulk)
   - Background job in future; synchronous in V1 is acceptable with smaller batch size.

3. **Due diligence generation**
   - Select:
     - operator
     - period
     - commodity
     - subset of batches
   - Click “Evaluate Risk”
   - Show results + option to “Export EUDR report”

---

## 10. Integration with FactorTrace & Other Regimes

Claude should design EUDR as **another regime module** that fits into the broader architecture:

- Use same:
  - multi-tenant patterns
  - logging patterns
  - testing patterns
- Keep abstractions (risk provider, scoring) separate and swappable
- Leave hooks for future cross-regime features:
  - e.g. linking emissions factors (CBAM/CSRD) to EUDR batches
  - regime enum / registry to show “this tenant uses CSRD + CBAM + EUDR”

---

## 11. Expectations from Claude Agentic Coder

When given this `eudr.md` plus the rest of the meta:

1. **Propose and implement DB schema:**
   - SQLAlchemy models + Alembic migrations for:
     - `eudr_commodity`
     - `eudr_operator`
     - `eudr_supply_site`
     - `eudr_batch`
     - `eudr_supply_chain_link`
     - `eudr_georisk_snapshot`
     - `eudr_due_diligence`
     - `eudr_due_diligence_batch_link`

2. **Implement services:**
   - `app/services/eudr_risk.py`
   - `app/services/eudr_geo.py` (optional) or integrated into `eudr_risk`
   - CRUD + high-level operations for sites, batches, links, DD

3. **Expose API:**
   - Under `/api/v1/eudr`
   - Pydantic schemas with clear regimes/IDs
   - OpenAPI doc updates

4. **Tests:**
   - `tests/test_eudr_models.py`
   - `tests/test_eudr_risk.py`
   - `tests/test_eudr_api.py`
   Cover:
   - risk scoring
   - georisk snapshot integration (mock provider)
   - due diligence evaluation

5. **Reports:**
   - Add EUDR export using same patterns as ESRS/CBAM
   - Ensure XHTML/iXBRL template can co-exist with other report templates

6. **Respect global meta:**
   - `DECISIONS.md` → multi-tenancy, database choices, architecture principles
   - `PERFORMANCE_BUDGET.md` → query count and latency budgets
   - `LEARNINGS.md` → reuse existing patterns for:
     - CSV ingestion
     - unit handling
     - logging and tests

---

## 12. Non-Goals for V1

To keep this shippable:

- No full integration with live satellite APIs in the first iteration  
  → use plugin-style provider with mocks or precomputed data
- No full-blown spatial database (PostGIS) requirement for V1  
  → accept `lat/lon` and simple polygons as text; can migrate later
- No complete legal automation for **all** EUDR documentation formats  
  → focus on due diligence summary + structured statement that can be attached to formal submissions

Focus: ** credible, auditable, structured EUDR due diligence engine** that can be expanded, not a research project.
