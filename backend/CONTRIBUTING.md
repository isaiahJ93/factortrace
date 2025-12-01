# Contributing to FactorTrace



FactorTrace is a **multi-regime regulatory compliance platform** for Tier 1 & 2 suppliers, with a roadmap toward **CSRD/ESRS, CBAM, EUDR, ISSB and beyond**.



This guide is for:



- **Isaiah** (founder / chief engineer)

- **AI assistants** (Claude Agentic Coder, ChatGPT, etc.)

- **Future engineers/contractors**

- Anyone extending FactorTrace with new regimes or capabilities



The goal of this document is to make work on FactorTrace:



- **Predictable** (same patterns every time)  

- **Safe** (no tenant leaks, no perf explosions)  

- **Fast** (AI + humans can ship new regimes in weeks, not months)



---



## 0. Before You Start – Read These



Always load/read these files **in this order** before making non-trivial changes:



1. `CLAUDE.md` – Project overview, architecture, domain context  

2. `DECISIONS.md` – Key architecture decisions & trade-offs  

3. `PERFORMANCE_BUDGET.md` – Non-negotiable performance targets  

4. `LEARNINGS.md` – Technical knowledge, gotchas, and patterns (Pint, EXIOBASE, XBRL, etc.)  

5. `plan.md` – Current sprint focus  

6. `roadmap.md` – Multi-regime vision (CSRD → CBAM → EUDR → ISSB → future regimes)  

7. `docs/api/*.md` – API contracts (especially `emissions-contract.md`, `voucher-purchase-contract.md`)  

8. `docs/regimes/*.md` – Regime specs (`cbam.md`, `eudr.md`, `issb.md`) if relevant to your task  



For AI tools: explicitly tell them to **load these files into context** before generating code.



---



## 1. Repository Structure



High-level layout (from repo root: `~/Documents/Scope3Tool`):



```text

Scope3Tool/

  backend/

    app/

      api/v1/endpoints/    # FastAPI routes (emissions, factors, reports, etc.)

      models/              # SQLAlchemy ORM models

      schemas/             # Pydantic v2 schemas

      services/            # Business logic (calculations, mapping, reports)

      ui.py                # Simple backend-driven UI endpoints

    data/

      mappings/            # YAML lookup/mapping files (DEFRA/EPA/EXIOBASE, sector maps)

      raw/                 # Raw datasets (DEFRA, EPA, EXIOBASE IOT ZIP, etc.)

    docs/

      api/                 # API contracts (emissions, voucher purchase, etc.)

      regimes/             # Regime specs (cbam.md, eudr.md, issb.md, etc.)

    scripts/               # Ingestion, seeding, tests, MCP tools

    templates/             # HTML/Jinja templates (calculator, reports, etc.)

    tests/                 # Python tests (calculation, coverage, reports, etc.)

    .claude/

      commands/            # Slash commands (/review, /ship-check, /perf-audit, etc.)

      skills/              # Auto-activated skills (regulatory-context, csv-processing)

    CLAUDE.md

    DECISIONS.md

    PERFORMANCE_BUDGET.md

    LEARNINGS.md

    plan.md

    roadmap.md

    memory.md

    verify_golden_path.py

    factortrace.db*        # Local SQLite DB (dev)

  

  frontend/                # New Next.js UI scaffold (v2+ UI target)

    app/

    components/

    lib/

    public/

    ...



  factortrace-frontend/    # Legacy/experimental Next.js UI (keep for reference/migration)

When in doubt: put new backend logic in backend/, and treat factortrace-frontend/ as legacy.









2. Local Setup







2.1 Backend (FastAPI + SQLite/Postgres)

cd backend



# Install dependencies

poetry install





Database

For local development (recommended):



export DATABASE_URL="sqlite:///./factortrace.db"



# Create / upgrade schema

poetry run alembic upgrade head

For PostgreSQL (staging/production-like):



export DATABASE_URL="postgresql://user:pass@localhost:5432/factortrace"

poetry run alembic upgrade head





Seed Emission Factors

You have tooling + data for DEFRA, EPA, EXIOBASE:



# Generic factor ingestion + seeds (use as documented in LEARNINGS.md)

poetry run python scripts/seed_master_factors.py



# For EXIOBASE-specific prep

poetry run python scripts/prepare_exiobase_spend_2020.py

poetry run python scripts/test_exiobase_e2e.py





Run Backend

poetry run uvicorn app.main:app --reload



# API docs

#   http://localhost:8000/docs

#   http://localhost:8000/redoc  (if enabled)







2.2 Tests



You already have a non-trivial test suite (calculation + coverage):



# Full suite

poetry run pytest -v



# Focused:

poetry run pytest tests/test_calculation_api.py -v

poetry run pytest tests/test_exiobase_spend.py -v

poetry run pytest tests/test_defra_coverage.py -v

poetry run pytest tests/test_epa_coverage.py -v

poetry run pytest tests/test_reports.py -v

poetry run pytest tests/test_ghg_protocol_scope3.py -v



# Golden path sanity check (end-to-end)

poetry run python verify_golden_path.py

Before merging/“shipping” anything: tests + golden path must pass.









2.3 Frontend (New UI)

cd frontend



npm install

npm run dev



# http://localhost:3000

The new frontend/ app is the future primary UI. factortrace-frontend/ is legacy and should be mined for components, then gradually retired.









3. Development Rules (Non-Negotiable)



These rules exist to prevent silent disasters at scale (tenant leaks, 30s APIs, broken regulators).







3.1 Multi-Tenancy & Security



Every tenant-owned record must:





Have a tenant_id column (indexed)

Be filtered by tenant_id in every query path

Be covered by tests that prove cross-tenant isolation



Bad:



# ❌ Never do this

emissions = db.query(Emission).all()

Good:



# ✅ Scoped to tenant

emissions = (

    db.query(Emission)

    .filter(Emission.tenant_id == current_user.tenant_id)

    .all()

)

Patterns:





Use current_user.tenant_id (or equivalent) everywhere you touch tenant data.

For security reasons, prefer 404 over 403 when a resource exists but belongs to another tenant (avoid leaking existence).



Use the /tenant-check Claude command on any file where you add/modify queries:



/tenant-check app/api/v1/endpoints/emissions.py app/services/ghg_calculation_service.py







3.2 Performance (See 

PERFORMANCE_BUDGET.md

)



You have explicit budgets. Respect them.



Typical targets (p95):





List endpoints: < 200ms

Single-resource reads: < 100ms

Writes (create/update/delete): < 300ms

CSV import:



1k rows: < 2s

10k rows: < 10s

50k rows: < 60s (streaming if needed)



Rules of thumb:





No N+1 queries. Use joinedload/selectinload when necessary.

Index foreign keys and commonly filtered columns (e.g., tenant_id, created_at).

Don’t pull entire tables into memory; paginate.



Use the /perf-audit command when touching hot paths:



/perf-audit app/services/ghg_calculation_service.py app/api/v1/endpoints/emissions.py







3.3 Testing Requirements



Every meaningful change must include tests:





Unit tests for individual calculation logic

Integration tests for APIs (FastAPI endpoints)

Security tests for tenant isolation

Regression tests for bugs that have occurred before



Targets:





Core services: ≥ 90% coverage

API endpoints: ≥ 80% coverage

Overall backend: ≥ 80% is the baseline



Before committing:



poetry run pytest -v

poetry run python verify_golden_path.py

If you break coverage significantly, either add tests or explicitly document why in LEARNINGS.md + commit message.









3.4 Contract-First API Design



No “endpoint first, docs later.”



Process:





Define the contract in docs/api/<resource>-contract.md:



Request and response schemas (shape, types, required fields)

Validation rules (ranges, enums, constraints)

Business rules

Error codes and semantics

Required tests

Implement:



Pydantic schemas in app/schemas/*.py

Service logic in app/services/*.py

Endpoints in app/api/v1/endpoints/*.py

Add tests:



tests/test_<resource>_api.py

Any logic-specific test files



Examples to model:





docs/api/emissions-contract.md

docs/api/voucher-purchase-contract.md

Existing emission API tests.







3.5 Data Governance & Datasets



Raw datasets live in backend/data/raw/

Mapping/config lives in backend/data/mappings/

Do not hardcode emission factors in Python files; always refer through mappings.

Very large data (e.g., EXIOBASE ZIP) should be:



Tracked intentionally (not duplicated)

Ideally managed with LFS in the future if needed.



Use LEARNINGS.md to capture any quirks (e.g., id formats, missing columns, known data issues).









4. Working With Regimes (CSRD → CBAM → EUDR → ISSB)



Core CSRD/ESRS functionality is your base. New regimes (CBAM, EUDR, ISSB) should be structured as modules that reuse patterns and infrastructure.



Regime specs live at:





docs/regimes/cbam.md

docs/regimes/eudr.md

docs/regimes/issb.md



These describe:





Scope & objectives

Required data model additions

Calculation logic

API surface

Reporting formats (PDF, XHTML/iXBRL)

Edge cases and risk points







4.1 Pattern: Adding a New Regime (Step-by-Step)



Use this for CBAM/EUDR/ISSB and any future regime (e.g., FuelEU, NIS2):







Step 1 – Spec

Create or update a spec:



backend/docs/regimes/<regime>.md

Include:





High-level description & regulatory references

Entities and data model changes

Calculation formulas (including units)

Required APIs & endpoints

Reporting templates and required outputs

Edge cases, risk factors, validation rules







Step 2 – Data Model & Migration

cd backend

poetry run alembic revision -m "Add <regime> tables"

# Edit migration if needed

poetry run alembic upgrade head

In app/models/:





Add new models (e.g., CbamProduct, EudrSupplySite, IssbScenario).

Ensure:



tenant_id present where applicable.

Proper FKs and indexes.







Step 3 – Schemas

In app/schemas/<regime>.py:





Define Base, Create, Update, Read models.

Use Pydantic v2 features as appropriate (e.g., model_config, field_validator).

Ensure from_attributes = True for ORM compatibility.







Step 4 – Services

In app/services/<regime>.py:





Implement core calculations (emissions, risk, scores, financial materiality, etc.).

Keep services pure where possible: given inputs + DB session, return structured results.

Log important decisions (e.g., which factors chosen when multiple could apply).







Step 5 – Endpoints

In app/api/v1/endpoints/<regime>.py:





Wire your API routes.

Enforce:



Auth

Tenant scoping

Validation

Follow patterns in existing endpoints (emissions, reports, emission_factors).



Update app/api/v1/api.py:



from app.api.v1.endpoints import cbam, eudr, issb



api_router.include_router(cbam.router, prefix="/cbam", tags=["CBAM"])

(and so on)







Step 6 – Reports & Templates

In templates/:





Add <regime>_report.html and, if needed, XHTML/iXBRL templates.

Mirror structure from existing reporting templates (calculator.html, etc.)



Integrate into app/services/reports.py (or a new module) so regime-specific reports:





Are generated consistently (HTML → PDF → XHTML/iXBRL)

Include meta-data (dataset used, factors, assumptions)







Step 7 – Tests

Create or extend tests:





tests/test_<regime>_models.py (if complex)

tests/test_<regime>_logic.py

tests/test_<regime>_api.py

Add security tests (cross-tenant isolation)

Add performance tests if regime involves bulk processing (e.g., 10k+ lines)







Step 8 – Verification

Run:



poetry run pytest -v

poetry run python verify_golden_path.py

Optionally add a regime-specific golden path (e.g., verify_cbam_path.py) once stable.







Step 9 – Docs & Commit

Update:





docs/regimes/<regime>.md with any implementation deviations

LEARNINGS.md with hard-earned insights

roadmap.md if timelines or stages shift



Commit with a conventional message:



git commit -m "feat(<regime>): add <regime> module with API, models, and reports"







5. Working With AI (Claude, ChatGPT, etc.)



FactorTrace is designed to be built with AI as your senior dev team. To keep that power under control:







5.1 Always Load the Right Context



For any serious coding session, instruct the AI:



Load these files:

CLAUDE.md, DECISIONS.md, PERFORMANCE_BUDGET.md, LEARNINGS.md, plan.md, roadmap.md, docs/api/*.md, docs/regimes/<regime>.md, backend/CONTRIBUTING.md.



This prevents:





Reinventing patterns

Violating perf or security rules

Inconsistent regime implementations







5.2 Prompt Pattern for Features



Example (CBAM):



You are working on FactorTrace, a multi-regime regulatory compliance platform.

Context loaded: CLAUDE.md, DECISIONS.md, PERFORMANCE_BUDGET.md, LEARNINGS.md, roadmap.md, docs/regimes/cbam.md, docs/api/emissions-contract.md, backend/CONTRIBUTING.md.



Task: Implement CBAM embedded emissions for steel imports as described in docs/regimes/cbam.md.



Requirements:





Follow multi-tenant patterns (tenant_id everywhere).

Respect performance budgets for bulk calculations (10k+ lines).

Implement: models, schemas, service, endpoints, tests, and basic report template.

Use the step-by-step process in CONTRIBUTING.md under “How to Add a New Regime”.



Return:





Migration snippet

Models

Schemas

Service functions

Endpoints

Tests

Any necessary updates to routers or docs.







5.3 Use the Slash Commands



You have several custom commands wired via .claude/commands:





/review – Deep code review (correctness, security, performance, style)

/ship-check – Pre-deploy / pre-merge quality gate

/perf-audit – Performance analysis of target files

/tenant-check – Scan for missing tenant filters

/emission-test – Help generate thorough tests for emissions logic

/csv-debug – Debug and harden CSV ingestion

/dockerize – Generate/inspect Docker deploy artefacts



Use them especially when:





You modify queries → /tenant-check

You touch hot paths → /perf-audit

You’re about to ship a chunk → /review + /ship-check







5.4 Keep Diffs Focused



Even with AI, keep PR-sized units:





1 feature/regime slice per branch

1 clear commit (or small chain) per slice

Avoid “mega-commits” combining refactors, new regimes, and data changes at once







6. Git Workflow







6.1 Branching



Use lightweight, descriptive branches:



git checkout -b feat/cbam-products

git checkout -b feat/eudr-risk-scoring

git checkout -b feat/issb-scenario-analysis



git checkout -b fix/tenant-leak-vouchers

git checkout -b fix/exiobase-factor-mapping



git checkout -b chore/update-defra-2025

git checkout -b docs/add-contributing-guide





6.2 Commit Messages



Conventional-ish commits:





feat: ... – new feature

feat(<regime>): ... – regime-specific feature

fix: ... – bug fix

chore: ... – dependency / housekeeping

docs: ... – documentation-only

refactor: ... – structural code changes without behavior change



Examples:



feat: add multi-tenant reports API

feat(cbam): implement product-level embedded emissions

fix(csv): handle German number formatting correctly

chore: update DEFRA 2024 emission factors

docs: document CBAM data model and calculation logic





6.3 Tags & Milestones



Use annotated tags for major milestones:



git tag -a v0.2-claude-optimized -m "Claude optimization system complete"

git tag -a v0.3-csrd-v1 -m "CSRD/ESRS V1 prod-ready"

git tag -a v0.4-cbam-beta -m "CBAM beta release"

git tag -a v1.0-multi-regime -m "CSRD + CBAM + EUDR prod"



git push origin --tags

This makes it trivial to show progress to investors/customers.









7. Code Style & Patterns







7.1 Python



Use type hints everywhere (inputs + return types).

Prefer small, pure functions in services where possible.

Keep FastAPI endpoints slim; push logic into app/services.

Use logging for important events (not prints).

Handle errors with clear exceptions → FastAPI handlers where needed.







7.2 Pydantic & Validation



Use Pydantic v2 style (model_config, field_validator, etc.).

Validate:



units

value ranges

date ranges

Normalize numeric input (via CSV skill + learnings) to avoid locale issues.







7.3 Frontend



For frontend/:





TypeScript, strongly typed API clients (lib/api/*).

Use React Query or equivalent for data fetching (planned).

Keep regulatory logic in the backend, not the frontend.







8. Checklists







8.1 Before You “Ship” Any Backend Change



CLAUDE.md, DECISIONS.md, PERFORMANCE_BUDGET.md skimmed

Changes respect multi-tenancy rules

No obvious N+1s or unbounded queries

Tests added/updated

poetry run pytest -v passes

poetry run python verify_golden_path.py passes

/review + /ship-check used on key files

Docs updated if behavior or API changed







8.2 Before You Call a Regime “Done” (e.g., CBAM)



Spec in docs/regimes/<regime>.md is up to date

Data model + migrations are applied and documented

Schemas and services cover required functionality

Endpoints are wired, documented, and tested

Reports generate correct structure (PDF + XHTML/iXBRL where applicable)

Performance budgets met on realistic data volumes

Tenant isolation verified for all regime data

Tests exist for:



Happy path

Edge cases

Security

Performance (if needed)







9. Questions & Ownership



Architecture or trade-offs? → DECISIONS.md

Performance concerns? → PERFORMANCE_BUDGET.md

Domain details & gotchas? → LEARNINGS.md

Regime details? → docs/regimes/*.md

High-level direction? → roadmap.md, plan.md



If you’re an AI assistant: follow this file and the referenced markdown files as your source of truth.

If you’re a human dev: follow the patterns, keep changes small, and leave the codebase cleaner than you found it.



Welcome to the FactorTrace multi-regime engine.

Ship carefully, but ship fast. 🚀
