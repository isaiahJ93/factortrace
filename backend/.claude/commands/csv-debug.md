# /csv-debug

You are helping me debug CSV import and emission factor ingestion for FactorTrace.

When I run this command, you should:

1. **Look specifically at:**
   - `scripts/ingest_factors_generic.py`
   - `data/mappings/*.yml`
   - `data/raw/*.csv`
   - Any recent error logs or stack traces I paste.

2. **Diagnose:**
   - Column mapping issues
   - Unit normalization problems
   - Dataset name / scope / category mismatches
   - Rows being skipped unexpectedly

3. **Propose:**
   - Minimal code changes
   - Targeted tests in `tests/` to lock in fixes
   - Logging improvements to make future debugging easier

Assume DEFRA, EPA, and EXIOBASE ingestion are all in scope.
