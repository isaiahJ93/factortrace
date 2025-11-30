






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

