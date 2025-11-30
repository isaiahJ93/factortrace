# FactorTrace Project Memory

## Current State

- **Architecture:** FastAPI + SQLAlchemy + Pydantic backend with CSV importer + reporting engine; targeting PostgreSQL in production.
- **Multi-tenancy:** Rules defined in `CLAUDE.md`, Phase 1 (hardening) is the current priority.
- **Agent context:**  
  - `CLAUDE.md` = source of truth for architecture & rules.  
  - `plan.md` = current 2-week sprint (CSV importer + tenant hardening).  
  - `.claude/skills/*` and `.claude/commands/*` = specialized helpers.

## Phase Focus

- **Current sprint:** CSV Importer + Multi-Tenant Hardening.
- **Primary goal:** Make the importer and core API **safe for real tenants** (no cross-tenant leakage) and robust for 50MB+ files.

---

## Known Issues & Blockers

- [ ] Some endpoints still missing `tenant_id` filters (Phase 1).
- [ ] Need to add database indexes on `tenant_id` columns (Phase 1).
- [ ] Safari file upload compatibility untested / incomplete (Phase 2).
- [ ] German number format (`1.234,56`) sanitization not yet wired into importer (Phase 4).

---

## Next Actions

1. Complete `/tenant-check` audit on all API endpoints (emissions, vouchers, payments, reports).
2. Add cross-tenant security tests for emissions, vouchers, payments (Tenant A/B isolation).
3. Add database migrations for `tenant_id` indexes on all tenant-owned tables.
4. Begin Phase 2 file upload implementation (size limits, encoding handling, Safari behaviour).

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
