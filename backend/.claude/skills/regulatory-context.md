# Regulatory Context Loader

**Trigger**: When working on emission factors, CSRD/ESRS, CBAM, or regulatory compliance code.

**Auto-load:**
- Always assume multi-tenant isolation is CRITICAL.
- DEFRA factors are activity-based (kgCO2e per unit).
- EXIOBASE factors are spend-based (kgCO2e per EUR).
- All currency must normalize to EUR with conversion tracking.
- All units must use Pint for safe conversion.
- German number format: 1.234,56 vs US: 1,234.56.

**Security reminders:**
- Every query MUST filter by `tenant_id`.
- Never trust user input for units or currency.
- Always sanitize before handing values to Pint / pandas.

**When generating code, prefer:**
- Service-layer calls over direct DB queries.
- Explicit type hints and Pydantic validation.
- Comprehensive error logging (no silent failures).
