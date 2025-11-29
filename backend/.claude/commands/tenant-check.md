# /tenant-check

You are performing a multi-tenancy security audit on FactorTrace.

When I run this command:

1. **Scan** any backend files I show you (FastAPI routes, services, models).

2. **Identify** any queries that:
   - Read, update, or delete tenant-owned data (emissions, vouchers, payments, reports, etc.)
   - Are missing a `tenant_id` filter tied to `current_user.tenant_id`.

3. **For each issue**, propose a concrete patch that:
   - Adds the correct `tenant_id` filter.
   - Updates or adds tests under `tests/` to assert no cross-tenant data leakage.

Use the conventions defined in CLAUDE.md for multi-tenant isolation.
