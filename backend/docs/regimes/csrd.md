# CSRD/ESRS E1 Climate Change Reporting Specification

> **Status**: V1 Production
> **Last Updated**: 2025-12-12
> **Regulation**: Directive 2022/2464 (Corporate Sustainability Reporting Directive)
> **Primary Standard**: ESRS E1 (Climate Change)

---

## 1. Overview & Legal Basis

### Regulatory Framework

The Corporate Sustainability Reporting Directive (CSRD) requires companies to report sustainability information according to the European Sustainability Reporting Standards (ESRS). FactorTrace implements ESRS E1 (Climate Change) for GHG emissions disclosure.

**Legal References:**
- Directive 2022/2464/EU (CSRD)
- Commission Delegated Regulation 2023/2772 (ESRS)
- ESRS E1: Climate Change (mandatory for all in-scope companies)

### Mandatory Scope

| Company Type | Threshold | First Reporting Year |
|--------------|-----------|---------------------|
| Large EU companies | >250 employees OR >€40M revenue OR >€20M assets | FY2024 (reports due 2025) |
| Listed SMEs | Listed on EU-regulated markets | FY2025 (reports due 2026) |
| Non-EU subsidiaries | Parent >€150M EU revenue | FY2024/2025 |
| Non-EU companies | >€150M EU revenue, EU subsidiary/branch | FY2028 |

### GHG Protocol Alignment

ESRS E1 requires GHG emissions reporting aligned with:
- GHG Protocol Corporate Standard (Scopes 1, 2, 3)
- GHG Protocol Scope 3 Standard (15 categories)
- ISO 14064-1:2018

---

## 2. V1 Scope

### Supported Emission Types

**Scope 1 - Direct Emissions:**
- Stationary combustion (boilers, furnaces, generators)
- Mobile combustion (company vehicles, fleet)
- Fugitive emissions (refrigerants, process leaks)
- Process emissions (chemical reactions, industrial processes)

**Scope 2 - Indirect Energy Emissions:**
- Location-based method (grid average factors)
- Market-based method (supplier-specific, RECs, PPAs)
- **ESRS E1 requires DUAL REPORTING** (both methods mandatory)

**Scope 3 - Value Chain Emissions (V1):**

| Category | Name | V1 Status | Calculation Method |
|----------|------|-----------|-------------------|
| 1 | Purchased Goods & Services | Supported | Activity or spend-based |
| 2 | Capital Goods | Deferred | - |
| 3 | Fuel & Energy Activities | Supported | WTT + T&D losses |
| 4 | Upstream Transportation | Supported | Distance or spend-based |
| 5 | Waste Generated | Supported | Waste-type specific |
| 6 | Business Travel | Supported | Distance-based |
| 7 | Employee Commuting | Supported | Survey + averages |
| 8 | Upstream Leased Assets | Deferred | - |
| 9 | Downstream Transportation | Supported | Distance-based |
| 10 | Processing of Sold Products | Deferred | - |
| 11 | Use of Sold Products | Supported | Product lifecycle |
| 12 | End-of-Life Treatment | Deferred | - |
| 13 | Downstream Leased Assets | Deferred | - |
| 14 | Franchises | Deferred | - |
| 15 | Investments | Deferred | - |

### Excluded from V1

- ESRS S1-S4 (Social standards) - Out of scope for emissions module
- ESRS G1 (Governance) - Out of scope for emissions module
- Scope 3 Categories 2, 8, 10, 12, 13, 14, 15 - Deferred to V2
- Biogenic emissions accounting - Deferred to V2
- Carbon removals/offsets tracking - Partial (evidence only)

---

## 3. Key Entities

### Data Model

| Entity | Type | tenant_id | Description |
|--------|------|-----------|-------------|
| `Emission` | Tenant-owned | Required (NOT NULL) | Individual emission records with activity data |
| `EmissionFactor` | Global reference | No | Shared emission factor database |
| `EvidenceDocument` | Tenant-owned | Required (NOT NULL) | Supporting documentation (invoices, meters, audits) |
| `DataQualityScore` | Tenant-owned | Required (NOT NULL) | Data quality assessment per emission record |
| `User` | Tenant-owned | Required (NOT NULL) | User who created/modified the record |

### Emission Model Fields

```
Emission:
  id: Integer (PK)
  tenant_id: String(36) FK → tenants.id (NOT NULL, indexed)
  user_id: Integer FK → users.id (nullable)

  # Classification
  scope: Enum(1, 2, 3) (NOT NULL, indexed)
  category: String(100) (NOT NULL, indexed)
  subcategory: String(100) (nullable)

  # Activity Data
  activity_value: Float (NOT NULL) - renamed from activity_data
  unit: String(50) (NOT NULL)

  # Emission Factor
  emission_factor_id: UUID FK → emission_factors.id (nullable)
  emission_factor_override: Float (nullable) - manual override
  emission_factor_source: String(200) (nullable)

  # Calculated Result
  calculated_co2e: Float (NOT NULL) - renamed from amount

  # Data Quality
  data_source: Enum(measured, calculated, estimated, default)
  data_quality_score: Integer(1-5)
  uncertainty_percentage: Float (nullable)

  # Context
  location: String(200) (nullable)
  country_code: String(2) (nullable)
  reporting_period_start: DateTime (nullable)
  reporting_period_end: DateTime (nullable)
  description: Text (nullable)

  # Verification
  is_verified: Boolean (default: false)
  verified_by: String(200) (nullable)
  verified_at: DateTime (nullable)

  # Audit
  created_at: DateTime (auto)
  updated_at: DateTime (auto)
  deleted_at: DateTime (nullable) - SOFT DELETE
```

### Composite Indexes (Tenant-First)

```sql
CREATE INDEX idx_emissions_tenant_scope ON emissions(tenant_id, scope);
CREATE INDEX idx_emissions_tenant_category ON emissions(tenant_id, category);
CREATE INDEX idx_emissions_tenant_created ON emissions(tenant_id, created_at);
CREATE INDEX idx_emissions_tenant_deleted ON emissions(tenant_id, deleted_at);
```

---

## 4. Emission Factor Sources

### Supported Datasets

| Dataset | Version | Coverage | Method | Update Frequency |
|---------|---------|----------|--------|------------------|
| DEFRA | 2024 | UK, EU default | Activity-based | Annual (June) |
| EPA | 2024 | US | Activity-based | Annual |
| EXIOBASE | 3.8.2 (2020) | Global | Spend-based | Periodic |

### GWP Values

| Source | Default | Notes |
|--------|---------|-------|
| IPCC AR5 | Yes | 100-year GWP, ESRS default |
| IPCC AR6 | Optional | Latest science, configurable |

### Factor Resolution Priority

1. **Tenant-specific override** (if `emission_factor_override` provided)
2. **Supplier-specific factor** (if linked via `emission_factor_id`)
3. **Country-specific factor** (DEFRA for GB, EPA for US)
4. **Regional fallback** (EU average, ROW)
5. **Global default** (DEFRA global factors)

---

## 5. Calculation Methodology

### Tier Hierarchy

| Tier | Name | Data Quality | Use Case |
|------|------|--------------|----------|
| Tier 1 | Primary/Measured | 5 (Excellent) | Direct measurement, meter data |
| Tier 2 | Calculated | 3-4 (Fair-Good) | Activity data × emission factors |
| Tier 3 | Estimated | 1-2 (Minimal-Poor) | Spend-based, extrapolation |

### Calculation Formulas

**Scope 1 & 2 (Activity-Based):**
```
calculated_co2e (kgCO2e) = activity_value × emission_factor × GWP_multiplier
calculated_co2e (tCO2e) = calculated_co2e (kgCO2e) / 1000
```

**Scope 3 Activity-Based:**
```
calculated_co2e = quantity × category_specific_factor
```

**Scope 3 Spend-Based (EXIOBASE):**
```
calculated_co2e = spend_eur × exiobase_sector_factor
```

**Currency Conversion (for spend-based):**
```
spend_eur = spend_original × fx_rate_to_eur
# Store: original_currency, conversion_rate, conversion_date
```

### Precision Requirements

| Metric | Precision | Example |
|--------|-----------|---------|
| Activity value | As provided | 1234.5678 |
| Emission factor | 6 decimal places | 0.233140 |
| Result (kgCO2e) | 4 decimal places | 287.8765 |
| Result (tCO2e) | 2 decimal places | 0.29 |
| Percentage | 1 decimal place | 12.5% |

---

## 6. Unit Handling (Pint Integration)

### Supported Units

| Category | Units | Base Unit |
|----------|-------|-----------|
| Mass | kg, t, tonne, lb, ton | kg |
| Energy | kWh, MWh, GJ, MJ, BTU, therm | kWh |
| Volume | L, m³, gal, ft³ | L |
| Distance | km, mi, m | km |
| Currency | EUR, USD, GBP | EUR |
| Composite | tonne-km, passenger-km, m²-year | as-is |

### Validation Rules

```python
# All units must be validated via Pint
from pint import UnitRegistry
ureg = UnitRegistry()

def validate_unit(unit_string: str) -> bool:
    try:
        ureg.parse_expression(unit_string)
        return True
    except:
        return False

# Reject unknown units with suggestions
# Example: "tons" → "Did you mean 'tonne' or 'ton'?"
```

### Auto-Conversion

- Convert to base units before calculation
- Store original unit + value for audit trail
- Convert result to tCO2e for aggregation

---

## 7. Number Sanitization

### Format Detection & Conversion

| Format | Example | Detection | Normalization |
|--------|---------|-----------|---------------|
| US/UK | 1,234.56 | Comma before dot | Remove commas |
| EU (DE, FR, IT) | 1.234,56 | Dot before comma | Replace . with '', , with . |
| No separators | 1234.56 | Single dot only | Pass through |
| Scientific | 1.23E+06 | Contains E/e | Parse as float |

### Implementation

```python
def sanitize_number(value: str | float | int, locale_hint: str = "auto") -> float:
    """
    Normalize numeric input to Python float.

    Args:
        value: Raw input (may be string with locale formatting)
        locale_hint: "US", "EU", or "auto" (detect from format)

    Returns:
        Normalized float value

    Raises:
        ValueError: If value cannot be parsed as a number
    """
    # Implementation handles:
    # - "1,234.56" (US) → 1234.56
    # - "1.234,56" (EU) → 1234.56
    # - "1234.56" → 1234.56
    # - "" or "N/A" → ValueError with clear message
```

### Required Application Points

- `POST /api/v1/emissions` - `activity_value` field
- `PUT /api/v1/emissions/{id}` - `activity_value` field
- CSV bulk upload - all numeric columns
- `/calculate` endpoints - `amount` field

---

## 8. Data Quality Scoring

### Score Definitions (1-5 Scale)

| Score | Level | Criteria | Examples |
|-------|-------|----------|----------|
| 5 | Excellent | Primary data, third-party verified | Calibrated meters + ISO 14064 verification |
| 4 | Good | Primary data, internal verification | Utility invoices + internal QA review |
| 3 | Fair | Secondary data, supplier-provided | Supplier emission reports, EPDs |
| 2 | Poor | Estimated, industry averages | EXIOBASE spend-based, sector averages |
| 1 | Minimal | Extrapolated, high uncertainty | Revenue proxies, peer benchmarks |

### Scoring Components

```python
def calculate_data_quality_score(emission: Emission) -> dict:
    """
    Calculate composite data quality score.

    Components:
    - source_quality (40%): Data source type
    - temporal_quality (20%): Data age/relevance
    - geographic_quality (20%): Location specificity
    - completeness (20%): Required fields populated
    """
    return {
        "total_score": 1-5,
        "source_quality": 1-5,
        "temporal_quality": 1-5,
        "geographic_quality": 1-5,
        "completeness": 1-5,
        "flags": ["missing_evidence", "outdated_factor", ...]
    }
```

### Automatic Adjustments

| Condition | Score Adjustment |
|-----------|-----------------|
| Evidence document attached | +1 |
| Third-party verification | +1 |
| Data older than 2 years | -1 |
| Spend-based calculation | Max score = 2 |
| Missing country_code | -1 |

---

## 9. API Contract

### Base Path

```
/api/v1/emissions/
```

### Source of Truth

`docs/api/emissions-contract.md` - Canonical API specification

### Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/` | Create emission record | Required |
| GET | `/` | List emissions (paginated) | Required |
| GET | `/{id}` | Get single emission | Required |
| PUT | `/{id}` | Update emission | Required |
| DELETE | `/{id}` | Soft-delete emission | Required |
| GET | `/summary` | Aggregated totals | Required |
| POST | `/calculate` | Calculate without saving | Required |
| GET | `/export/csv` | Export to CSV | Required |
| POST | `/bulk-upload` | Bulk import | Required |

### Request/Response Standards

**Create Request (POST /):**
```json
{
  "activity_value": 1234.56,
  "unit": "kWh",
  "emission_factor_id": "uuid-or-null",
  "emission_factor_override": null,
  "date": "2024-11-30",
  "scope": 2,
  "category": "electricity",
  "activity_type": "Electricity - Grid Average",
  "country_code": "DE",
  "notes": "Optional description"
}
```

**Success Response (201):**
```json
{
  "id": 123,
  "tenant_id": "tenant_abc",
  "activity_value": 1234.56,
  "unit": "kWh",
  "emission_factor_id": "uuid",
  "calculated_co2e": 0.29,
  "scope": 2,
  "category": "electricity",
  "date": "2024-11-30",
  "data_quality_score": 4,
  "created_at": "2024-11-30T10:00:00Z",
  "updated_at": "2024-11-30T10:00:00Z"
}
```

**List Response (GET /):**
```json
{
  "items": [...],
  "page": 1,
  "page_size": 25,
  "total": 123,
  "total_pages": 5
}
```

**Error Response (422):**
```json
{
  "detail": [
    {
      "field": "unit",
      "message": "Unknown unit 'tons'. Did you mean 'tonne'?"
    },
    {
      "field": "activity_value",
      "message": "Expected a number, got 'N/A'."
    }
  ]
}
```

### Critical Requirements

1. **Soft Delete**: Use `deleted_at` timestamp, never hard delete
2. **Pagination**: Always return `{items, page, page_size, total}` wrapper
3. **Field Names**: Match this spec exactly (not legacy names)
4. **Tenant Scoping**: All queries filter by `tenant_id`
5. **Cross-Tenant**: Return 404 (not 403) to avoid leaking existence

---

## 10. ESRS E1 Disclosure Mapping

### Mandatory Disclosures

| ESRS Ref | Requirement | FactorTrace Implementation |
|----------|-------------|---------------------------|
| E1-6 | Gross Scope 1, 2, 3 GHG emissions | `GET /emissions/summary` aggregated by scope |
| E1-6 | Scope 2 location-based | Filter: `scope=2, method=location_based` |
| E1-6 | Scope 2 market-based | Filter: `scope=2, method=market_based` |
| E1-6 | Scope 3 by category | `GET /emissions/summary?scope=3&group_by=category` |
| E1-7 | GHG removals and storage | `EvidenceDocument.type = OFFSET/REMOVAL` |
| E1-8 | GHG intensity per revenue | `total_co2e / tenant.annual_revenue` |
| E1-9 | Methodology disclosure | Data quality scores + emission factor sources |

### Intensity Metrics

```python
# Revenue intensity (required)
ghg_intensity_revenue = total_tco2e / revenue_eur_million

# Optional industry-specific
ghg_intensity_employee = total_tco2e / fte_count
ghg_intensity_product = total_tco2e / units_produced
```

### Comparative Disclosure

ESRS E1 requires year-over-year comparison:
- Current year emissions
- Previous year emissions (restated if methodology changed)
- Base year emissions (for target tracking)

---

## 11. Output Formats

### Regulatory Filing (iXBRL/XHTML)

| Element | Format | Template |
|---------|--------|----------|
| Primary output | XHTML with embedded iXBRL tags | `templates/csrd/esrs_e1_report.xhtml` |
| Taxonomy | ESRS 2024 XBRL taxonomy | EFRAG published |
| Validation | ESEF/ESRS validation rules | Pre-submission check |

### Human-Readable (PDF)

| Element | Format | Template |
|---------|--------|----------|
| Report | PDF generated from XHTML | WeasyPrint conversion |
| Charts | SVG embedded | Scope breakdown, trends |
| Tables | Formatted data tables | Emission details |

### Data Export (CSV)

| Column | Description |
|--------|-------------|
| id | Record identifier |
| tenant_id | Tenant identifier |
| scope | 1, 2, or 3 |
| category | Emission category |
| activity_value | Activity quantity |
| unit | Unit of measurement |
| calculated_co2e | Calculated tCO2e |
| emission_factor | Factor used |
| data_quality_score | 1-5 score |
| date | Activity date |
| created_at | Record creation timestamp |

---

## 12. Security (Non-Negotiable)

### Tenant Isolation

```python
# ALL queries must use tenant helpers
from app.core.tenant import tenant_query, get_tenant_record, delete_tenant_record

# List query
emissions = tenant_query(db, Emission, current_user.tenant_id).all()

# Single record (returns 404 if wrong tenant)
emission = get_tenant_record(db, Emission, emission_id, current_user.tenant_id)

# Delete (validates tenant ownership)
delete_tenant_record(db, Emission, emission_id, current_user.tenant_id)
```

### Create Operations

```python
# Always set tenant_id from authenticated user
new_emission = Emission(
    tenant_id=current_user.tenant_id,  # NEVER from request body
    ...
)
```

### Cross-Tenant Access

```python
# Return 404 (not 403) to avoid information leakage
if emission.tenant_id != current_user.tenant_id:
    raise HTTPException(status_code=404, detail="Emission not found")
```

### Audit Logging

All CRUD operations must log:
- `user_id`: Who performed the action
- `tenant_id`: Which tenant
- `action`: CREATE, UPDATE, DELETE
- `timestamp`: When
- `changes`: What changed (for updates)

---

## 13. Implementation Gap Closure

### Required Fixes to Align Implementation with Spec

| # | Gap | Current State | Required Change | Priority |
|---|-----|---------------|-----------------|----------|
| 1 | Soft Delete | Hard delete via `delete_tenant_record()` | Add `deleted_at` column, filter in all queries | HIGH |
| 2 | Field Names | `activity_data`, `amount` | Rename to `activity_value`, `calculated_co2e` | MEDIUM |
| 3 | Pagination | Returns raw list | Wrap in `{items, page, page_size, total}` | HIGH |
| 4 | Number Sanitization | Not wired | Apply `sanitize_number()` to `activity_value` | MEDIUM |
| 5 | Pint Validation | Only in `/calculate` | Add to POST/PUT `/emissions` | MEDIUM |
| 6 | emission_factor_id | Float value stored | Add optional FK to `emission_factors` | LOW |

### Migration Path

1. **Phase 1** (Non-Breaking):
   - Add `deleted_at` column (nullable)
   - Add `activity_value` as alias for `activity_data`
   - Add `calculated_co2e` as alias for `amount`
   - Update queries to exclude `deleted_at IS NOT NULL`

2. **Phase 2** (API v1.1):
   - Add pagination wrapper
   - Wire `sanitize_number()`
   - Add Pint validation

3. **Phase 3** (Breaking - API v2):
   - Remove legacy field names
   - Require `emission_factor_id` FK

---

## Appendix A: ESRS E1 Data Points Checklist

| Data Point | ESRS Ref | FactorTrace Field | Status |
|------------|----------|-------------------|--------|
| Gross Scope 1 | E1-6.44 | `SUM(calculated_co2e) WHERE scope=1` | Implemented |
| Gross Scope 2 (location) | E1-6.46 | `SUM(calculated_co2e) WHERE scope=2 AND method='location'` | Implemented |
| Gross Scope 2 (market) | E1-6.47 | `SUM(calculated_co2e) WHERE scope=2 AND method='market'` | Implemented |
| Gross Scope 3 | E1-6.51 | `SUM(calculated_co2e) WHERE scope=3` | Implemented |
| Scope 3 by category | E1-6.52 | `GROUP BY category` | Implemented |
| GHG intensity (revenue) | E1-8 | Calculated metric | Implemented |
| Methodology | E1-9 | `emission_factor_source`, `data_quality_score` | Implemented |
| Base year | E1-6.40 | Configurable per tenant | Planned |
| Restatements | E1-6.43 | Audit trail | Planned |

---

## Appendix B: Emission Factor Lookup Example

```python
# Example: German electricity (Scope 2)
factor = get_factor(
    db,
    scope=2,
    category="electricity",
    activity_type="Electricity - Grid Average",
    country_code="DE",
    year=2024,
    dataset="DEFRA_2024"
)
# Returns: 0.35 kgCO2e/kWh

# Example: Spend-based IT services (Scope 3)
factor = get_factor(
    db,
    scope=3,
    category="spend_based",
    activity_type="Computer programming, consultancy and related activities",
    country_code="DE",
    year=2020,
    dataset="EXIOBASE_2020"
)
# Returns: 0.25 kgCO2e/EUR
```
