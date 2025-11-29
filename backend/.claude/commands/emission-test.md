# /emission-test

You help me generate and refine tests for FactorTrace emission calculations.

When I run this command:

1. **Look at:**
   - `app/services/emission_factors.py`
   - Emission-related models and schemas
   - Existing tests under `tests/` for emissions and factors.

2. **Generate:**
   - Test cases that verify:
     - Correct factor selection (scope, category, activity_type, country, year, dataset).
     - Proper fallback to GLOBAL when needed.
     - Basic sanity checks (no negative factors, reasonable ranges).

3. **Where appropriate**, include specific test examples covering:
   - DEFRA 2024 factors
   - EPA 2024 Hub factors
   - EXIOBASE 2020 spend-based factors.
