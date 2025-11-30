
# Performance Budget – FactorTrace



These are non-negotiable performance targets that all code (including AI-generated) must respect, especially for CSV ingestion and reporting.



If a proposed approach is likely to violate these, it must be flagged and optimized.



---



## 1. API Response Times (Backend, p95)



- GET list endpoints (small datasets, e.g. reports list):  

  - Target: < 200ms

- GET single resource:  

  - Target: < 100ms

- POST/PUT/DELETE (standard CRUD):  

  - Target: < 300ms

- Heavy operations (kick off long-running jobs):  

  - Synchronous part: < 500ms (enqueue job, return 202 / job id).



---



## 2. CSV Import & Validation



Assume CSVs up to 50MB and 50k rows for suppliers.



- 1,000 rows:  

  - Target: < 2 seconds

- 10,000 rows:  

  - Target: < 10 seconds

- 50,000 rows:  

  - Target: < 60 seconds (with streaming + chunked validation)



Rules:



- Must stream / chunk large files, not load entire content into memory at once.

- Number sanitization + Pint validation must be vectorized where possible (avoid Python loops).

- Error reporting:

  - Row/column-level errors must still be captured without blowing up memory.



---



## 3. Emission Factor Lookups



For typical supplier workloads (hundreds to thousands of lookups per report):



- Single factor lookup (warm cache):  

  - Target: < 5ms per lookup.

- Bulk factor lookup (10k rows):  

  - Target: < 2 seconds using vectorized/optimized paths.



Rules:



- Use indexes on (`dataset`, `country_code`, `year`, `scope`, `category`).

- Prefer batched queries or in-memory maps over 10k individual DB round-trips.

- For hot paths, consider per-tenant caches (in-memory/Redis).



---



## 4. Reporting (PDF + XHTML/iXBRL)



For a typical supplier report:



- PDF generation:  

  - Target: < 5 seconds per report.

- XHTML/iXBRL generation:  

  - Target: < 8 seconds per report (more complex templates allowed).



Rules:



- Do heavy work in background jobs where needed.

- Avoid re-parsing large datasets per request; reuse cached factor data where possible.

- Ensure that exporting functions are pure / side-effect-free aside from logging.



---



## 5. Database Constraints



- No N+1 query patterns in high-traffic/list endpoints.

- Pagination mandatory for list endpoints:

  - Default page size: 25–50.

  - Max page size: 100.

- All foreign key and high-cardinality filter columns must be indexed:

  - `tenant_id`, `dataset`, `year`, `country_code`, `scope`, etc.



---



## 6. Memory Usage



- CSV processing (50MB file):  

  - Target peak memory: < 500MB.

- Standard API requests:  

  - Target per-request memory: < 50MB.



Rules:



- Avoid building huge in-memory Python lists/dicts if streaming is possible.

- Prefer generators / chunked processing where appropriate.



---



## 7. Frontend Performance (Target for V1)



- Initial dashboard load:  

  - Target: < 2 seconds on a typical EU connection.

- CSV upload UX:

  - Progress bar updates frequently; UI stays responsive.

- Bundle size:

  - Target: < 500KB gzipped for main app bundle.



---



## 8. How to Use This Budget



When generating or reviewing code:



1. Check new features against this budget.

2. If something is likely to break it:

   - Flag: "This approach may violate PERFORMANCE_BUDGET.md for X."

   - Propose alternative strategies (streaming, caching, batching, etc.).

3. For critical paths (CSV import, factor lookups, reporting):

   - Use `/perf-audit` to identify concrete bottlenecks.

