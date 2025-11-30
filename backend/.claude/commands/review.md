






/review



Comprehensive code review helper for FactorTrace.



When I run this command on one or more files (for example:

/review app/api/v1/emissions.py app/services/emissions_service.py):









1. Security



Check for:





Missing tenant_id filters on any tenant-owned data (emissions, vouchers, payments, reports, uploads).

Direct DB access from route handlers that bypasses service layer patterns described in CLAUDE.md.

Unvalidated user input:



Path/query/body values used directly in DB queries.

Unsanitized CSV data passed straight into Pint/pandas.

Authentication/authorization gaps:



Endpoints that should require auth but do not.

Actions not checked against current tenant / user permissions.



Output:





🚨 Critical security issues with:



File + line references.

Concrete patch suggestions.







2. Performance



Check for:





N+1 query patterns (loops doing DB queries repeatedly).

Missing indexes on hot filter columns (e.g. tenant_id, dataset, year, country_code).

Inefficient pandas usage (row-wise apply for huge data, unnecessary copies).

Loading entire large files or tables into memory when streaming/chunking is needed.



Use PERFORMANCE_BUDGET.md as the baseline and flag any likely violations.



Output:





⚠️ Performance warnings with:



Why it is a problem.

Suggested refactors or patterns (chunking, caching, batching).







3. Code Quality & Maintainability



Check for:





Missing type hints on public functions / methods.

Inconsistent naming or confusing abstractions.

Missing or weak error handling (especially around I/O, CSV, external services).

Duplicated logic that could be moved to a helper/service.



Output:





💡 Suggestions for improving clarity, structure, and reuse.







4. Testing & Coverage



Check for:





Missing tests for new branches / edge cases.

No negative tests (invalid input, cross-tenant attempts, malformed CSV).

Gaps in integration tests (e2e flows: upload → calculate → report).

For critical paths, ensure tests align with contracts in docs/api/*.md.



Output:





Test checklist:



Which tests exist.

Which tests are missing and should be added.







5. Regulatory & Domain Alignment



Given FactorTrace is a Global Regulatory SaaS, also check:





Alignment with decisions in DECISIONS.md (do not contradict architecture choices without explanation).

Proper use of units, factors, and datasets:



No magic constants where a factor lookup is expected.

Logging & auditability for key actions (calculations, report generation, voucher redemption).







Output Format



Return a structured review:





🚨 Critical (must fix before merge)

⚠️ Warnings (should fix soon)

💡 Suggestions (nice to have)

✅ What’s good (patterns worth repeating)



Where possible, include:





File + line numbers.

Example patches (diff-style) for high-impact fixes.

