# ISSB Regime Specification – FactorTrace

Status: Draft → Target V1 in 6–9 weeks  
Owner: Isaiah + Claude Agentic Coder  
Primary Users: CFOs, Group Controllers, Sustainability/Finance leads, Investor Relations  

---

## 1. What ISSB Is (Working Model for the System)

ISSB (IFRS S1 + S2) = **general sustainability + climate-related financial disclosures**.

For FactorTrace, we treat ISSB as:

> “The financial overlay that connects emissions and transition/physical risk data to revenue, EBITDA, assets, and enterprise value, and outputs investor-grade disclosures.”

We don’t need to replicate every paragraph of IFRS S1/S2. We need a **structured, automatable core** that:

1. Links **emissions + climate risks** to **financial metrics**  
2. Performs **materiality assessment** (what is financially material?)  
3. Supports **scenario analysis** (1.5°C, 2°C, 3°C paths)  
4. Generates **ISSB-aligned disclosure statements** in a reusable format (PDF/XHTML/iXBRL)  

---

## 2. Supported Scope in V1

### 2.1 Standards Covered

V1 focus:

- **IFRS S2 (Climate-related Disclosures)** – primary scope
- With a **minimal IFRS S1 wrapper** so it doesn’t look “climate-only”:

  - Governance
  - Strategy
  - Risk management
  - Metrics & targets

We don’t implement all topical standards – we build:

- A **climate module** that is ISSB-aligned
- A **generic disclosure engine** we can reuse for future topics (biodiversity, water, etc.)

### 2.2 Use Cases

Target V1 use cases:

- “We have emissions data (Scope 1/2/3) from FactorTrace, we want to produce:
  - Risk + financial exposure summaries
  - Scenario analysis view (e.g. revenue at risk, carbon cost at carbon prices)
  - Targets & KPIs dashboards
  - Disclosures that can be dropped straight into an annual report / integrated report / sustainability report.”

---

## 3. Data Model Additions

We add a **financial + risk + scenario layer** on top of existing emissions.

### 3.1 Core New Tables

1. **issb_reporting_unit**
   - `id`
   - `tenant_id`
   - `name` (e.g. “Group”, “EU operations”, “Manufacturing segment”)
   - `description`
   - `currency` (ISO code)
   - `consolidation_method` (`full`, `equity`, `proportionate`)

2. **issb_financial_metric**
   - `id`
   - `reporting_unit_id`
   - `period_start`, `period_end`
   - `metric_type` (enum/string: `revenue`, `ebitda`, `ebit`, `capex`, `opex`, `assets`, `liabilities`, `carbon_price_exposure`, etc.)
   - `value` (numeric)
   - `currency`
   - `segment` (optional string – product line/geography)
   - `notes` (text)

3. **issb_climate_risk_exposure**
   - `id`
   - `reporting_unit_id`
   - `period_start`, `period_end`
   - `risk_type` (`physical`, `transition`)
   - `subtype` (e.g. `acute`, `chronic` for physical; `policy`, `technology`, `market`, `reputation` for transition)
   - `description`
   - `time_horizon` (`short`, `medium`, `long`)
   - `financial_impact_type` (`revenue_downside`, `cost_upside`, `asset_impairment`, etc.)
   - `impact_range_low` (numeric)
   - `impact_range_high` (numeric)
   - `currency`
   - `qualitative_likelihood` (`low`, `medium`, `high`, `very_high`)
   - `linked_to_emissions` (bool)
   - `linked_scope` (`scope1`, `scope2`, `scope3`, `mixed`, nullable)

4. **issb_target**
   - `id`
   - `reporting_unit_id`
   - `target_type` (`emissions_intensity`, `absolute_emissions`, `renewables_share`, `capex_alignment`, etc.)
   - `scope` (`scope1`, `scope2`, `scope3`, `combined`, nullable)
   - `base_year` (int)
   - `target_year` (int)
   - `base_value` (numeric)
   - `target_value` (numeric)
   - `unit` (`tCO2e`, `tCO2e/revenue`, `%`, etc.)
   - `status` (`not_started`, `in_progress`, `on_track`, `off_track`, `achieved`)
   - `notes`

5. **issb_scenario**
   - `id`
   - `tenant_id`
   - `name` (e.g. “1.5C_high_policy”, “2C_base_case”, “3C_no_policy”)
   - `description`
   - `temperature_pathway` (text – link to NGFS/IEA type)
   - `carbon_price_path_json` (JSON string: year → price)
   - `policy_assumptions` (text)
   - `market_assumptions` (text)
   - `created_at`, `updated_at`

6. **issb_scenario_result**
   - `id`
   - `scenario_id`
   - `reporting_unit_id`
   - `period_start`, `period_end`
   - `metric_type` (`revenue`, `ebitda`, `cost_of_carbon`, `capex_required`, `stranded_assets`, etc.)
   - `base_case_value` (numeric)
   - `scenario_value` (numeric)
   - `delta_value` (numeric)
   - `currency`
   - `notes`

7. **issb_materiality_assessment**
   - `id`
   - `reporting_unit_id`
   - `period_start`, `period_end`
   - `topic` (`climate`, `water`, `biodiversity`, etc. — for V1 mostly `climate`)
   - `impact_materiality_score` (0–100)
   - `financial_materiality_score` (0–100)
   - `material` (bool)
   - `justification` (text)
   - `methodology_reference` (text: “2D matrix”, “multi-criteria”, etc.)

8. **issb_disclosure_statement**
   - `id`
   - `tenant_id`
   - `reporting_unit_id`
   - `period_start`, `period_end`
   - `standard` (e.g. `IFRS_S1`, `IFRS_S2`)
   - `section` (`governance`, `strategy`, `risk_management`, `metrics_targets`)
   - `status` (`draft`, `approved`, `archived`)
   - `headline_summary` (text – short)
   - `body_markdown` (text – rich detail)
   - `generated_by_system` (bool)
   - `last_edited_by` (user id / string)
   - `created_at`, `updated_at`

### 3.2 Linking to Existing Data

We must link ISSB layer to:

- **Emissions** (existing `emissions` tables / models)
- **Entities / tenants**

We can add linking tables if needed, e.g.:

**issb_emissions_link**

- `id`
- `reporting_unit_id`
- `emission_record_id` (FK to existing emission schema)
- `scope` (`scope1`, `scope2`, `scope3`)
- `weight` (numeric – used to apportion emissions into specific units/segments)

This allows:

- Multiple reporting units referencing the same emissions records
- Segment-level breakdowns

---

## 4. Materiality & Risk Models (V1)

ISSB expects **materiality assessment** and **risk descriptions**. We build:

- A simple, transparent **materiality scoring model**
- A structured way to store climate risk exposures

### 4.1 Materiality Assessment Model

For each topic (in V1: `climate`):

Inputs:

- Impact dimension:
  - GHG emissions magnitude (absolute + intensity)
  - Value chain coverage (Scope 1/2/3)
  - Geographic exposure to climate risk (we can later pull from EUDR / geo modules)
- Financial dimension:
  - Revenue/EBITDA contribution of high-emitting activities
  - Capex/opex alignment with transition

We define a 0–100 scoring system:

- `impact_materiality_score` (0–100)
- `financial_materiality_score` (0–100)

Claude should implement:

- A simple function in `app/services/issb_materiality.py`:

  - `assess_materiality(inputs) -> IssbMaterialityAssessment`

Where `inputs` is a Pydantic model containing:

- Emissions summary (tCO2e by scope, by segment)
- Financial metrics (revenue, EBITDA by segment)
- Optional flags (e.g. “emissions-intensive sector”)

Materiality thresholds (configurable, but default):

- Material if:
  - `impact_score >= 50` **or**
  - `financial_score >= 50`

These thresholds must be easy to change.

---

## 5. Scenario Analysis (V1)

Scenario analysis is one of the ISSB “hard” parts. We make it tractable and automatable.

### 5.1 Modelling Approach

We don’t build a full-blown IAM. We do:

1. **Carbon price exposure modelling**
   - For each reporting unit:
     - estimate emissions per unit of revenue/product
     - apply scenario-specific carbon price paths to get:
       - projected carbon cost
       - impact on EBITDA/margins

2. **Revenue / cost sensitivity**
   - Allow simple elasticity inputs:
     - e.g. `% change in demand per unit increase in carbon price` for certain segments
   - Compute scenario revenue / cost adjustments

3. **Capex alignment**
   - Track capex required to meet targets under each scenario (input or computed)

### 5.2 Inputs to Scenario Model

For each **scenario**:

- `carbon_price_path_json`
  - e.g. `{2025: 60, 2030: 100, 2035: 150}`
- Risk narrative (qualitative, stored as text)
- Optional default elasticity parameters per sector

For each **reporting unit**:

- Emissions (Scope 1/2/3) per period (from existing FactorTrace)
- Financial metrics:
  - baseline revenue
  - baseline EBITDA
  - baseline costs
- Sector / activity tags

### 5.3 Outputs (issb_scenario_result)

Per scenario + reporting unit + period:

- `cost_of_carbon` (per year)
- `delta_ebitda` (scenario vs base)
- `revenue_delta` (if elasticity used)
- `stranded_assets` (if we add this later)
- `notes` (for textual explanation)

Claude should:

- Implement scenario calc in `app/services/issb_scenarios.py`
- Support both:
  - deterministic calcs (no Monte Carlo needed in V1)
  - placeholders where your existing Monte Carlo engine could hook in later

---

## 6. API Design for ISSB

Base path:

- `/api/v1/issb/`

### 6.1 Key Endpoints

1. **Reporting Units**

   - `POST /issb/reporting-units/`
   - `GET /issb/reporting-units/`
   - `GET /issb/reporting-units/{id}`

2. **Financial Metrics**

   - `POST /issb/financial-metrics/`
   - `GET /issb/financial-metrics/`
     - Filters: `reporting_unit_id`, period, `metric_type`, `segment`

3. **Climate Risk Exposures**

   - `POST /issb/climate-risks/`
   - `GET /issb/climate-risks/`
     - Filter by `risk_type`, `reporting_unit_id`, period

4. **Targets**

   - `POST /issb/targets/`
   - `GET /issb/targets/`

5. **Scenarios**

   - `POST /issb/scenarios/`
   - `GET /issb/scenarios/`
   - `GET /issb/scenarios/{id}`

6. **Scenario Evaluation**

   - `POST /issb/scenarios/{id}/evaluate`
     - Inputs:
       - `reporting_unit_ids` list
       - `period_start`, `period_end`
     - Outputs:
       - creates `issb_scenario_result` rows
   - `GET /issb/scenario-results/`
     - Filter by `scenario_id`, `reporting_unit_id`, period

7. **Materiality Assessment**

   - `POST /issb/materiality-assessments/compute`
     - Inputs:
       - `reporting_unit_id`
       - `period_start`, `period_end`
       - optional overrides
     - Logic:
       - gathers emissions + financials
       - runs materiality model
       - persists `issb_materiality_assessment`
   - `GET /issb/materiality-assessments/`

8. **Disclosure Statements**

   - `POST /issb/disclosures/generate`
     - Generate draft ISSB disclosures for:
       - `reporting_unit_id`
       - `period_start`, `period_end`
       - `standard` (`IFRS_S2` initially)
     - Uses underlying data (risks, scenarios, targets, materiality) to build:
       - `headline_summary`
       - `body_markdown`
   - `GET /issb/disclosures/`
   - `GET /issb/disclosures/{id}`
   - `PATCH /issb/disclosures/{id}`
     - Allow manual edits to text

9. **Exports**

   - `GET /issb/disclosures/{id}/export`
     - Query param: `format=pdf|xhtml`
     - Exports ISSB climate section ready for inclusion in reports

All endpoints:

- Strictly **tenant-scoped**
- Respect performance budgets in `PERFORMANCE_BUDGET.md`

---

## 7. ISSB Report / Disclosure Template

We define a flexible template for ISSB climate disclosures aligned with IFRS S2:

### 7.1 Sections

1. **Governance**
   - Textual summary of:
     - oversight by Board / management
     - committees
   - For V1, user-provided text, optionally stored in `issb_disclosure_statement`.

2. **Strategy**
   - Material climate risks & opportunities:
     - from `issb_climate_risk_exposure`
   - Time horizons:
     - short / medium / long
   - Links to financials:
     - exposures to revenue / EBITDA, capex

3. **Risk Management**
   - Description of:
     - identification
     - assessment
     - management  
   - For V1, partly user-input + some structured output summarizing risk inventory.

4. **Metrics & Targets**
   - Emissions metrics:
     - tCO2e by scope
     - intensities (e.g. tCO2e / revenue)
   - Financial metrics:
     - revenue exposed to high climate risk
     - capex alignment
   - Targets:
     - from `issb_target`
     - on-track/off-track status

5. **Scenario Analysis**
   - Key scenarios from `issb_scenario`
   - Summaries from `issb_scenario_result`, e.g.:
     - delta EBITDA under each scenario
     - cost of carbon
   - Short qualitative explanation of resilience.

### 7.2 Output Types

As with other regimes:

- PDF
- XHTML/iXBRL
- Structured JSON (for API consumers)

Claude should:

- Create templates `templates/issb_climate_disclosure.html` and `.xhtml`
- Reuse the same export pipeline already used for ESRS/CSRD exports

---

## 8. Validation & Edge Cases

Claude must add tests to cover:

1. **Missing financials**
   - If financial data is missing for a given period:
     - Materiality assessment should:
       - fall back gracefully
       - mark `financial_materiality_score` as “unknown” or use default logic
     - Disclosures should indicate “data incomplete” where relevant.

2. **Emissions but tiny revenue**
   - High emissions, very low revenue cases:
     - ensure logic still behaves (no divide-by-zero for intensity)
     - mark as potentially highly material on impact side even if financials are small.

3. **Multiple reporting units**
   - Group vs segment vs geography:
     - ensure scenario + materiality calculations can run per-unit
     - avoid double counting when aggregating.

4. **Extreme scenarios**
   - Very high carbon prices:
     - ensure no numeric overflow / absurd negative EBITDA without explanation
     - maintain result clamping and clear notes.

5. **Performance**
   - Running scenarios over many reporting units and periods should:
     - stay within budgets from `PERFORMANCE_BUDGET.md`
     - avoid N+1 queries (aggregate emissions / financials smartly).

---

## 9. UX / Workflow Expectations

High-level ISSB flows:

1. **Setup**
   - Define reporting units (group, business segments)
   - Link existing emissions to those units (direct or via mapping table)
   - Input or import financial metrics per unit & period.

2. **Risk & Materiality**
   - Enter climate risks:
     - either via UI or via CSV/API
   - Run **materiality assessment** for climate topic:
     - “Compute ISSB climate materiality for FY2025”

3. **Scenarios**
   - Define 2–3 scenarios (1.5°C, 2°C, 3°C)
   - Run scenario evaluation:
     - `scenario_id`, `reporting_unit_ids`, `period_range`

4. **Disclosure Generation**
   - Generate draft disclosure for IFRS S2:
     - `generate` → `edit` → `approve` → `export`

The frontend can be built later; the backend needs to be ready with:

- Clean, composable endpoints
- Clear data contracts

---

## 10. Integration with FactorTrace & Other Regimes

ISSB is a **cross-cutting overlay**:

- **CSRD/ESRS**:
  - Already provides emissions, governance, risk, metrics, targets
  - You can reuse or adapt ESRS fields for ISSB narrative
- **CBAM/EUDR** (future):
  - Their risk outputs can be fed in as inputs for ISSB risk + materiality

Claude should:

- Reuse:
  - logging
  - multi-tenancy enforcement
  - testing style
- Avoid duplication:
  - If ESRS already has a target model, either:
    - reuse and extend, or
    - design mapping between ESRS target and ISSB target

---

## 11. Expectations from Claude Agentic Coder

Given `issb.md` plus the global meta, Claude should:

1. **Design & implement DB models + migrations**
   - `issb_reporting_unit`
   - `issb_financial_metric`
   - `issb_climate_risk_exposure`
   - `issb_target`
   - `issb_scenario`
   - `issb_scenario_result`
   - `issb_materiality_assessment`
   - `issb_disclosure_statement`
   - optional `issb_emissions_link`

2. **Add services**
   - `app/services/issb_materiality.py`
   - `app/services/issb_scenarios.py`
   - possibly `app/services/issb_disclosures.py`

3. **Wire up API**
   - Under `/api/v1/issb/`
   - Pydantic schemas with clear field names and docstrings
   - Respect multi-tenant isolation

4. **Create tests**
   - `tests/test_issb_models.py`
   - `tests/test_issb_materiality.py`
   - `tests/test_issb_scenarios.py`
   - `tests/test_issb_api.py`

5. **Export templates**
   - Add ISSB disclosure templates using existing reporting infra
   - Ensure XHTML/iXBRL output is compatible with rest of system

6. **Respect global conventions**
   - Follow `DECISIONS.md` for architecture & security
   - Respect `PERFORMANCE_BUDGET.md`
   - Reuse patterns captured in `LEARNINGS.md` (Pint, CSV patterns, testing style, etc.)

---

## 12. Non-Goals for V1

To keep ISSB V1 **shippable**:

- No full integration of all ISSB topical standards (focus on climate)  
- No heavy Monte Carlo or advanced climate-economy modelling (deterministic scenarios are enough)  
- No full integration with external financial consolidation systems (inputs can be CSV/API-based)  

Goal:  
A **credible, auditable, investor-grade ISSB climate disclosure engine** that:

- connects emissions + financial data  
- performs basic scenario + materiality analysis  
- outputs structured disclosures ready for annual reports and digital filing  
