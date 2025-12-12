# FactorTrace Development Plan

## Current Status: Multi-Regime Platform COMPLETE

**Last Updated**: 2025-12-13
**Status**: All foundational work complete. Ready for production deployment.

---

## Completed Phases

### Phase 1: Multi-Tenant Security Hardening ✅ COMPLETE
- Created Tenant model, added tenant_id to all 8 tenant-owned models
- Alembic migration for multi-tenant schema
- Rewrote auth layer (JWT → tenant_id extraction)
- Created tenant helper functions (tenant_query, get_tenant_record)
- Updated all CSRD endpoints with tenant filtering
- 11 tenant isolation tests passing

### Phase 2: CBAM Module ✅ COMPLETE
- 5 SQLAlchemy models (CBAMFactorSource, CBAMProduct, CBAMDeclaration, CBAMDeclarationLine, CBAMInstallation)
- Alembic migration with tenant-first indexes
- Pydantic schemas with EORI/CN code validation
- 12 API endpoints (CRUD + calculate + breakdown)
- Router registered at /api/v1/cbam/
- 134 CBAM products seeded (CN codes for all V1 categories)

### Phase 3: EUDR Module ✅ COMPLETE
- 8 SQLAlchemy models with geospatial + supply chain graph
- Alembic migration with geo indexes
- Pydantic schemas with GeoJSON validation
- 37 API endpoints including:
  - Supply chain traversal (BFS + cycle detection)
  - Risk assessment (refresh-risk, evaluate)
  - Due diligence workflow
- Router registered at /api/v1/eudr/
- 55 EUDR commodities seeded (7 categories + derivatives)

### Phase 4: ISSB Module ✅ COMPLETE
- 8 SQLAlchemy models (ReportingUnit, FinancialMetric, ClimateRiskExposure, Target, Scenario, ScenarioResult, MaterialityAssessment, DisclosureStatement)
- 15 enums for type safety
- Alembic migration with tenant-first indexes
- ~40 API endpoints including scenario analysis, double materiality, disclosure generation
- Router registered at /api/v1/issb/
- Full report generation (PDF/JSON)

### Phase 5: CSRD Hardening ✅ COMPLETE
- GAP 1: Soft delete (deleted_at column)
- GAP 3: Pagination wrapper (PaginatedResponse)
- GAP 4: Number sanitization (EU/US format handling)
- GAP 5: Pint unit validation in CREATE
- GAP 6: emission_factor_id FK for audit traceability
- GAP 7: Audit logging (AuditLog model + service)
- Comprehensive CSRD spec (docs/regimes/csrd.md)

### Phase 6: Report Generation ✅ COMPLETE
- CSRD/ESRS E1 reports (XHTML/PDF)
- CBAM declaration exports (PDF/CSV)
- EUDR due diligence reports (PDF/CSV)
- ISSB disclosure statements (PDF/JSON)
- Full report generation service

### Phase 7: Deployment Infrastructure ✅ COMPLETE
- Dockerfile (multi-stage, Python 3.11, WeasyPrint deps)
- docker-compose.yml (API + PostgreSQL + Redis)
- .env.example with all variables documented
- /health and /ready endpoints (K8s probes)
- Rate limiting, request ID, security headers

### Phase 8: CI/CD Pipeline ✅ COMPLETE
- .github/workflows/ci.yml (lint, test, build, security scan)
- .github/workflows/deploy.yml (GHCR push, staging/prod deploy)
- Codecov integration
- Multi-platform Docker builds (amd64/arm64)

### Phase 9: Emission Factor Data ✅ COMPLETE
- EXIOBASE 2020: 8,361 factors (spend-based Scope 3)
- DEFRA 2024: 1,262 factors (UK GHG)
- EPA 2024: 58 factors (US GHG)
- CBAM_DEFAULT: 23 factors
- **Total: 9,704 production-ready emission factors**

---

## Final Platform Stats

| Metric | Value |
|--------|-------|
| Models | 30+ |
| API Endpoints | 100+ |
| Tests Passing | 206 |
| Emission Factors | 9,704 |
| Regulatory Regimes | 4 (CSRD, CBAM, EUDR, ISSB) |
| Export Formats | 5 (XHTML, PDF, CSV, JSON, iXBRL) |

---

## Next Sprint: Production & Enterprise Features

**Duration**: 2 weeks
**Goal**: Production deployment and enterprise-ready features

### Priority 1: Production Deployment
- [ ] Deploy to staging environment
- [ ] Configure production PostgreSQL
- [ ] Set up monitoring (Datadog/Sentry)
- [ ] Configure CDN for static assets
- [ ] SSL/TLS certificate setup

### Priority 2: Frontend Integration
- [ ] Connect Next.js frontend to backend APIs
- [ ] Implement auth flow (JWT + tenant selection)
- [ ] Build dashboard with regime switcher
- [ ] CSV upload with validation UI
- [ ] Report generation and download

### Priority 3: Enterprise Features
- [ ] Webhook system for async notifications
- [ ] Bulk import API (async with progress)
- [ ] Admin API for tenant management
- [ ] API rate limiting per tenant tier
- [ ] Usage tracking and billing hooks

### Priority 4: Customer Onboarding
- [ ] Stripe webhook hardening
- [ ] Voucher redemption flow
- [ ] Self-service tenant signup
- [ ] Onboarding wizard UI
- [ ] Documentation portal

---

## Future Roadmap (Post-Launch)

### Q1 2025
- FuelEU Maritime regime
- Enhanced iXBRL validation (ESRS taxonomy)
- Multi-language report generation

### Q2 2025
- NIS2 compliance module
- Advanced analytics dashboard
- API v2 with GraphQL option

### Q3 2025
- White-label partner portal
- Mobile companion app
- Real-time collaboration features

---

## Architecture Notes

All regimes are **ADDITIVE** (new tables only, zero changes to existing Emission model):
- Multi-tenant security pattern replicates cleanly across all regimes
- Foundation supports unlimited future regime expansion
- Lazy-loading router pattern for feature flags

---

## Reference Commands

- Run security audit: `/tenant-check`
- Debug CSV issues: `/csv-debug`
- Profile performance: `/perf-audit`
- Generate emissions tests: `/emission-test`
- Help with Docker setup: `/dockerize`
- Pre-ship quality gate: `/ship-check`
