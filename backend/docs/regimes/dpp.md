# Digital Product Passport (DPP) - ESPR Regulation

**Status:** Coming Q1 2026
**Regulation:** EU Ecodesign for Sustainable Products Regulation (ESPR) 2024/1781

## Overview

The Digital Product Passport is an EU requirement mandating machine-readable product information throughout the lifecycle. It enables circularity, repairability tracking, and carbon footprint transparency at the product level.

## Timeline

| Product Category | Compliance Deadline | Priority |
|-----------------|---------------------|----------|
| Batteries (EV/industrial) | February 2027 | HIGH |
| Textiles | 2028 | MEDIUM |
| Electronics | 2030 | MEDIUM |
| Construction products | 2030 | LOW |
| All regulated products | 2030+ | FUTURE |

## Data Model Outline

### Product
```
Product {
  id: UUID
  gtin: string              // Global Trade Item Number
  batch_id: string
  manufacturer_id: string
  product_category: enum    // BATTERY, TEXTILE, ELECTRONICS, etc.
  production_date: date
  production_facility: string
  qr_code_url: string       // Link to passport
}
```

### Materials & Composition
```
MaterialComposition {
  product_id: UUID
  material_name: string
  percentage: float
  recycled_content_pct: float
  origin_country: string
  certified: boolean
  certification_body: string
}
```

### Lifecycle & Carbon
```
LifecycleData {
  product_id: UUID
  carbon_footprint_kg: float
  manufacturing_emissions: float
  transport_emissions: float
  use_phase_emissions: float
  end_of_life_emissions: float
  methodology: string       // PEF, ISO 14067, etc.
  verification_status: enum
}
```

### Circularity
```
CircularityInfo {
  product_id: UUID
  repairability_score: int  // 0-10
  recyclability_pct: float
  disassembly_instructions_url: string
  spare_parts_available: boolean
  expected_lifetime_years: int
}
```

## API Structure (Future)

```
POST   /api/v1/dpp/passports              # Create passport
GET    /api/v1/dpp/passports/{id}         # Get passport by ID
GET    /api/v1/dpp/passports/gtin/{gtin}  # Lookup by GTIN
PATCH  /api/v1/dpp/passports/{id}         # Update passport
GET    /api/v1/dpp/passports/{id}/qr      # Generate QR code

POST   /api/v1/dpp/passports/{id}/materials      # Add material
POST   /api/v1/dpp/passports/{id}/lifecycle      # Add lifecycle data
POST   /api/v1/dpp/passports/{id}/circularity    # Add circularity info

GET    /api/v1/dpp/categories             # List product categories
GET    /api/v1/dpp/verify/{qr_token}      # Public verification endpoint
```

## Integration Points

### With CBAM
- DPP carbon footprint data can feed CBAM embedded emissions
- Shared material origin tracking
- Cross-reference CN codes for covered products

### With EUDR
- Material origin (country) feeds deforestation risk
- Geolocation data from DPP → EUDR compliance
- Timber/rubber products overlap

### With CSRD/Scope 3
- Product-level emissions aggregate to company Scope 3
- Supplier DPPs provide Category 1 (purchased goods) data
- Enables bottom-up emissions accounting

## QR Code Requirements

Per ESPR requirements:
- Unique identifier per product/batch
- Links to machine-readable passport (JSON-LD or similar)
- Must be durable (printed, etched, or embedded)
- Accessible to consumers, repair shops, and regulators

## Implementation Notes

### Phase 1 (Q1 2026)
- Battery DPP support only
- Basic passport CRUD
- QR generation
- Manual data entry

### Phase 2 (2027)
- Textile DPP templates
- Bulk import from PLM systems
- API integrations (SAP, Oracle)

### Phase 3 (2028+)
- Full product category coverage
- Automated LCA integration
- Blockchain verification (optional)
- Consumer-facing portal

## Pricing Model

| Tier | Volume | Price/passport |
|------|--------|----------------|
| Starter | 1-100 | EUR 2.00 |
| Business | 101-1000 | EUR 1.50 |
| Enterprise | 1000+ | EUR 1.00 |
| Self-serve single | 1 | EUR 200 (with wizard) |

## References

- [ESPR Regulation 2024/1781](https://eur-lex.europa.eu/eli/reg/2024/1781)
- [EU Battery Regulation 2023/1542](https://eur-lex.europa.eu/eli/reg/2023/1542)
- [Product Environmental Footprint (PEF)](https://environment.ec.europa.eu/strategy/pef_en)
