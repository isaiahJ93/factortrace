# FactorTrace Project Memory

## Current State

- **Architecture:** FastAPI + SQLAlchemy + Pydantic backend with CSV importer + reporting engine; targeting PostgreSQL in production.
- **Multi-tenancy:** Fully implemented - all tenant-owned models have tenant_id, all endpoints tenant-scoped.
- **Multi-regime platform:** CBAM, EUDR, and ISSB modules complete with full API coverage.
- **Agent context:**
  - `CLAUDE.md` = source of truth for architecture & rules.
  - `plan.md` = current sprint plan.
  - `.claude/skills/*` and `.claude/commands/*` = specialized helpers.

## Phase Focus

- **Current sprint:** Multi-Regime Platform Build (CBAM, EUDR, ISSB).
- **Primary goal:** Complete regulatory regime implementations with tenant isolation.

---

## Session: 2025-12-12 - Multi-Regime Platform Build (Marathon Session)

### Completed:

**Phase 1: Multi-Tenant Security Hardening**
- Created Tenant model, added tenant_id to all 8 tenant-owned models
- Alembic migration for multi-tenant schema
- Rewrote auth layer (JWT → tenant_id extraction)
- Created tenant helper functions (tenant_query, get_tenant_record)
- Updated all CSRD endpoints with tenant filtering
- 11/11 tenant isolation tests passing

**Phase 2: CBAM Module (Complete)**
- 5 SQLAlchemy models (CBAMFactorSource, CBAMProduct, CBAMDeclaration, CBAMDeclarationLine, CBAMInstallation)
- Alembic migration with tenant-first indexes
- Pydantic schemas with EORI/CN code validation
- 12 API endpoints (CRUD + calculate + breakdown)
- Router registered at /api/v1/cbam/

**Phase 3: EUDR Module (Complete)**
- 8 SQLAlchemy models with geospatial + supply chain graph
- Alembic migration with geo indexes
- Pydantic schemas with GeoJSON validation
- 37 API endpoints including supply chain traversal (BFS + cycle detection), risk assessment, due diligence workflow
- Router registered at /api/v1/eudr/

**Phase 4: ISSB Module (Complete)**
- 8 SQLAlchemy models (ReportingUnit, FinancialMetric, ClimateRiskExposure, Target, Scenario, ScenarioResult, MaterialityAssessment, DisclosureStatement)
- 15 enums for type safety
- Alembic migration with tenant-first indexes
- ~40 API endpoints including scenario analysis, double materiality, disclosure generation
- Router registered at /api/v1/issb/

### Architecture Validated:
- All regimes are ADDITIVE (new tables only, zero changes to existing Emission model)
- Multi-tenant security pattern replicates cleanly across all regimes
- Foundation supports unlimited future regime expansion
- Lazy-loading router pattern for feature flags

### Commits:
- feat: add multi-tenant security infrastructure
- fix: correct model field mappings + passing tenant isolation tests
- feat: complete CBAM module - models, migration, schemas, API
- feat: add EUDR data layer - models, migration, schemas
- feat: complete EUDR module - 37 API endpoints with supply chain traversal
- feat: complete ISSB module - 8 models, 40 API endpoints, scenario analysis

### Stats:
- 29 new models across 4 regimes
- 100+ API endpoints
- ~8,000+ lines of code
- 11/11 tenant isolation tests passing

---

## API Endpoint Summary

| Regime | Prefix | Endpoints | Key Features |
|--------|--------|-----------|--------------|
| CSRD | /emissions, /vouchers, etc. | ~20 | Core Scope 3 reporting |
| CBAM | /api/v1/cbam/ | 12 | EU carbon border adjustment |
| EUDR | /api/v1/eudr/ | 37 | Deforestation-free supply chains |
| ISSB | /api/v1/issb/ | ~40 | Climate financial disclosures |

---

## Known Issues & Blockers

- [x] ~~Some endpoints still missing `tenant_id` filters~~ (RESOLVED)
- [x] ~~Need to add database indexes on `tenant_id` columns~~ (RESOLVED - included in migrations)
- [ ] Safari file upload compatibility untested / incomplete.
- [ ] German number format (`1.234,56`) sanitization not yet wired into importer.
- [ ] Regime-specific isolation tests (CBAM, EUDR, ISSB) not yet written.
- [ ] Reference data seeding needed (CBAM CN codes, EUDR commodities).

---

## Next Session Priorities

1. Regime-specific isolation tests (CBAM, EUDR, ISSB)
2. Seed reference data (CBAM CN codes, EUDR commodities)
3. Report templates (iXBRL/PDF for each regime)
4. Frontend integration
5. Production deployment prep

---

## Reference Commands

- Run security audit: **`/tenant-check`**
- Debug CSV issues: **`/csv-debug`**
- Profile performance: **`/perf-audit`**
- Generate emissions tests: **`/emission-test`**
- Help with Docker backend setup: **`/dockerize`**

---

## How to Use This Memory

When working on FactorTrace, always:

1. Load `CLAUDE.md`, `plan.md`, and `memory.md` as context.
2. Confirm which Phase from `plan.md` is active.
3. Use the commands above to drive focused work on the repo.
