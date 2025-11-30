# /perf-audit

Analyze performance bottlenecks in FactorTrace.

When I run this command:

1. **Profile** the code for:
   - Database N+1 query patterns.
   - Missing indexes on frequently filtered columns (e.g. `tenant_id`, `dataset`, `year`).
   - Inefficient pandas operations (row-wise loops, unnecessary copies).
   - Loading large data fully into memory instead of streaming/chunking.

2. **Identify** hotspots specifically around:
   - CSV import and validation.
   - Emission factor lookups at scale.
   - Report generation paths (PDF/XHTML/iXBRL).

3. **Recommend** optimizations, such as:
   - SQL query improvements and index suggestions.
   - Pandas chunking/streaming strategies.
   - Caching strategies (per-tenant factor cache, FX rate cache).
   - Offloading heavy work to background jobs.

4. **Estimate** impact of each optimization (e.g., "≈2× faster", "≈50% less memory").

Focus on highest-impact, lowest-effort wins first, keeping codebase maintainable and production-grade.
