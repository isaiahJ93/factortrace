# FactorTrace Project Memory

## Current State

- **Architecture:** FastAPI + SQLAlchemy + Pydantic backend; targeting PostgreSQL in production.
- **Multi-tenancy:** Fully implemented - all tenant-owned models have tenant_id, all endpoints tenant-scoped.
- **Multi-regime platform:** CSRD, CBAM, EUDR, and ISSB modules complete with full API coverage.
- **Agent context:**
  - `CLAUDE.md` = source of truth for architecture & rules.
  - `plan.md` = current sprint plan.
  - `.claude/skills/*` and `.claude/commands/*` = specialized helpers.

## Phase Focus

- **Current status:** Multi-Regime Platform Build COMPLETE
- **Next priority:** Production deployment and enterprise features

---

## Session: 2025-12-13 - Multi-Regime Platform Build (Marathon Session)

### Completed:

**Phase 1: Multi-Tenant Security Hardening**
- Created Tenant model, added tenant_id to all 8 tenant-owned models
- Alembic migration for multi-tenant schema
- Rewrote auth layer (JWT → tenant_id extraction)
- Created tenant helper functions (tenant_query, get_tenant_record)
- Updated all CSRD endpoints with tenant filtering
- 11 tenant isolation tests passing

**Phase 2: CBAM Module (Complete)**
- 5 SQLAlchemy models (CBAMFactorSource, CBAMProduct, CBAMDeclaration, CBAMDeclarationLine, CBAMInstallation)
- Alembic migration with tenant-first indexes
- Pydantic schemas with EORI/CN code validation
- 12 API endpoints (CRUD + calculate + breakdown)
- Router registered at /api/v1/cbam/
- 134 CBAM products seeded (CN codes for all V1 categories)

**Phase 3: EUDR Module (Complete)**
- 8 SQLAlchemy models with geospatial + supply chain graph
- Alembic migration with geo indexes
- Pydantic schemas with GeoJSON validation
- 37 API endpoints including:
  - Supply chain traversal (BFS + cycle detection)
  - Risk assessment (refresh-risk, evaluate)
  - Due diligence workflow
- Router registered at /api/v1/eudr/
- 55 EUDR commodities seeded (7 categories + derivatives)
- Full report generation (PDF/CSV)

**Phase 4: ISSB Module (Complete)**
- 8 SQLAlchemy models (ReportingUnit, FinancialMetric, ClimateRiskExposure, Target, Scenario, ScenarioResult, MaterialityAssessment, DisclosureStatement)
- 15 enums for type safety
- Alembic migration with tenant-first indexes
- ~40 API endpoints including scenario analysis, double materiality, disclosure generation
- Router registered at /api/v1/issb/
- Full report generation (PDF/JSON)

**Phase 5: CSRD Hardening**
- Created docs/regimes/csrd.md (comprehensive spec matching CBAM/EUDR/ISSB)
- GAP 1: Soft delete (deleted_at column)
- GAP 3: Pagination wrapper (PaginatedResponse)
- GAP 4: Number sanitization (EU/US format handling)
- GAP 5: Pint unit validation in CREATE
- GAP 6: emission_factor_id FK for audit traceability
- GAP 7: Audit logging (AuditLog model + service)
- Report generation (ESRS E1 XHTML/PDF)

**Phase 6: Emission Factor Data**
- EXIOBASE 2020: 8,361 factors (spend-based Scope 3)
- DEFRA 2024: 1,262 factors (UK GHG)
- EPA 2024: 58 factors (US GHG)
- CBAM_DEFAULT: 23 factors
- Total: 9,704 production-ready emission factors

**Phase 7: Deployment Infrastructure**
- Dockerfile (multi-stage, Python 3.11, WeasyPrint deps)
- docker-compose.yml (API + PostgreSQL + Redis)
- .env.example with all variables documented
- /health and /ready endpoints (K8s probes)
- Rate limiting, request ID, security headers

**Phase 8: CI/CD Pipeline**
- .github/workflows/ci.yml (lint, test, build, security scan)
- .github/workflows/deploy.yml (GHCR push, staging/prod deploy)
- Codecov integration
- Multi-platform Docker builds (amd64/arm64)

### Architecture Validated:
- All regimes are ADDITIVE (new tables only, zero changes to existing Emission model)
- Multi-tenant security pattern replicates cleanly across all regimes
- Foundation supports unlimited future regime expansion

### Final Stats:
- 30+ models
- 100+ API endpoints
- 206 tests passing (0 failures)
- 9,704 emission factors
- 4 regulatory regimes (CSRD, CBAM, EUDR, ISSB)
- 5 export formats (XHTML, PDF, CSV, JSON, iXBRL)

### Commits (this session):
- feat: add multi-tenant security infrastructure
- fix: correct model field mappings + passing tenant isolation tests
- feat: complete CBAM module - models, migration, schemas, API
- feat: add EUDR data layer - models, migration, schemas
- feat: complete EUDR module - 37 API endpoints with supply chain traversal
- feat: complete ISSB module - 8 models, 40 API endpoints, scenario analysis
- feat: CSRD hardening Phase 1 + Phase 2
- feat: complete security test suite + iXBRL validation - 167 tests passing
- feat: add reference data seeds for CBAM, EUDR, and emission factors
- feat: complete report generation service - CSRD/ESRS + CBAM exports
- feat: complete deployment infrastructure - Docker + production hardening
- feat: complete platform - all reports, CI/CD, 9,704 emission factors

---

## Next Session Priorities

1. Push to GitHub: `git push origin main`
2. Deploy to staging environment
3. GAP 2: Field alignment (breaking change, v2)
4. GAP 8: iXBRL output validation against ESRS taxonomy
5. Frontend integration
6. Stripe webhook hardening
7. Customer onboarding flow

---

## API Endpoint Summary

| Regime | Prefix | Endpoints | Key Features |
|--------|--------|-----------|--------------|
| CSRD | /emissions, /vouchers, etc. | ~20 | Core Scope 3 reporting |
| CBAM | /api/v1/cbam/ | 12 | EU carbon border adjustment |
| EUDR | /api/v1/eudr/ | 37 | Deforestation-free supply chains |
| ISSB | /api/v1/issb/ | ~40 | Climate financial disclosures |

---

## Reference Commands

- Run security audit: `/tenant-check`
- Debug CSV issues: `/csv-debug`
- Profile performance: `/perf-audit`
- Generate emissions tests: `/emission-test`
- Help with Docker backend setup: `/dockerize`

---

## How to Use This Memory

When working on FactorTrace, always:

1. Load `CLAUDE.md`, `plan.md`, and `memory.md` as context.
2. Confirm which Phase from `plan.md` is active.
3. Use the commands above to drive focused work on the repo.
