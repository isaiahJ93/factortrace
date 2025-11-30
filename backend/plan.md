# FactorTrace Development Plan

## Current Sprint: CSV Importer + Multi-Tenant Hardening

**Duration**: 2 weeks (10 working days)  
**Goal**: Production-ready CSV importer with bulletproof tenant isolation.

---

## Phase 1: Multi-Tenant Security Hardening (Days 1–2)

**Status**: 🔄 IN PROGRESS

### Tasks
- [ ] Audit all `/api/v1/emissions` endpoints for `tenant_id` filters.
- [ ] Audit all `/api/v1/vouchers` endpoints for `tenant_id` filters.
- [ ] Audit all `/api/v1/payments` endpoints for `tenant_id` filters.
- [ ] Add cross-tenant access tests (create Tenant A/B data, assert isolation).
- [ ] Run `/tenant-check` on all modified files.
- [ ] (Optional) Add a pre-commit hook for `tenant_id` validation.

### Success Criteria
- All queries include a `tenant_id` filter.
- Tests prove no cross-tenant leakage.
- (If implemented) pre-commit hook catches violations.

---

## Phase 2: CSV Importer – File Upload (Days 3–4)

**Status**: ⏸️ BLOCKED (waiting for Phase 1)

### Tasks
- [ ] File size validation (< 50MB, reject with clear error).
- [ ] Safari compatibility: chunked upload with progress bar.
- [ ] Support `.csv`, `.xlsx`, `.xls` formats.
- [ ] Handle encoding issues (UTF-8, ISO-8859-1).
- [ ] Store upload metadata in DB (filename, size, `tenant_id`, timestamp).

### Success Criteria
- 50MB file uploads work on Safari without freezing.
- Clear error messages for rejected files.
- All uploads scoped to `tenant_id`.

---

## Phase 3: CSV Importer – Column Mapping UI (Days 5–6)

**Status**: ⏸️ BLOCKED (waiting for Phase 2)

### Tasks
- [ ] Auto-detect columns from CSV headers.
- [ ] Drag-and-drop column mapping interface.
- [ ] Preview first 10 rows with mapped columns.
- [ ] Save mapping state to localStorage (auto-resume).
- [ ] Validate mappings before processing (required fields present).

### Tech Stack
- React with `useState` (or equivalent) for mapping state.
- Web Workers for CSV parsing (prevent UI freeze).
- localStorage for state persistence.

### Success Criteria
- User can map arbitrary CSV columns to FactorTrace fields.
- Preview shows correct data.
- Mapping state survives browser refresh.

---

## Phase 4: CSV Importer – Validation Engine (Days 7–8)

**Status**: ⏸️ BLOCKED (waiting for Phase 3)

### Tasks
- [ ] Sanitize numbers: German (1.234,56) vs US (1,234.56).
- [ ] Validate units with Pint (reject unknown units).
- [ ] Validate currency codes (ISO 4217).
- [ ] Validate dates (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD).
- [ ] Cell-level error display:  
  `"Row 45, Column 'Diesel': Expected number, got 'N/A'"`.
- [ ] "Fix automatically" suggestions for common errors.

### Backend Processing (sketch)
```python
# Use pandas with explicit dtype control
df = pd.read_csv(file, dtype={"activity_value": str})

# Sanitize before Pint
df["activity_value_clean"] = df["activity_value"].apply(sanitize_number)

# Validate with Pint
for idx, value in df["activity_value_clean"].items():
    try:
        ureg.Quantity(value).to(canonical_unit)
    except Exception as e:
        errors.append({
            "row": idx,
            "column": "activity_value",
            "message": str(e),
        })
```

### Success Criteria
- All validation errors shown with specific row/column.
- No silent failures.
- Validation completes in < 5 seconds for 10,000 rows (target).

---

## Phase 5: Testing & Production Hardening (Days 9–10)

**Status**: ⏸️ BLOCKED (waiting for Phase 4)

### Tasks
- [ ] End-to-end test: upload → map → validate → import.
- [ ] Load test: 10,000 row CSV.
- [ ] Edge case tests: malformed data, empty cells, wrong types.
- [ ] Security test: attempt to upload malicious CSV.
- [ ] Performance profiling: identify bottlenecks.
- [ ] Add monitoring/logging for production.

### Success Criteria
- All tests pass.
- Performance acceptable (< 10s for 10k rows end-to-end).
- Production-ready error handling.

---

## Known Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Safari file upload fails > 40MB even with chunking | HIGH | Fall back to server-side chunking API |
| German/US number detection is ambiguous | MEDIUM | Add manual format selector in UI |
| Pint doesn't recognize obscure units | MEDIUM | Allow manual unit mapping with admin approval |
| Validation too slow for large files | HIGH | Use Web Workers + streaming validation |

---

## Post-Sprint: Next Features (Not in current 2-week scope)

1. **EXIOBASE integration** (spend-based factors).
2. **Multi-regime reports** (CBAM, ISSB, EUDR).
3. **Voucher workflow** (credit packs, supplier portals).
4. **PDF generation** (e.g. WeasyPrint pipeline).
5. **iXBRL export** (ESRS E1 compliance).
