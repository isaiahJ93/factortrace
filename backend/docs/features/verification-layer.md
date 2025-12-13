# Report Verification Layer

**Status:** Proposed
**Priority:** Medium (post-MVP)
**Dependencies:** Report generation, PDF service

## Purpose

Create legally defensible compliance reports with cryptographic proof of:
1. **Content integrity** - Report hasn't been modified since generation
2. **Timestamp** - When the report was generated
3. **Authorship** - Who generated the report (tenant/user)

This enables:
- Regulatory submissions with tamper-evident proof
- Auditor verification without contacting FactorTrace
- Customer trust through verifiable authenticity

## Components

### 1. Content Hash

SHA-256 hash of report payload (emissions data + metadata).

```
content_hash = SHA256(
  canonical_json(
    company_profile +
    emissions_data +
    methodology_notes +
    generated_at
  )
)
```

**Properties:**
- Deterministic (same input = same hash)
- Tamper-evident (any change = different hash)
- Fast to compute
- No external dependencies

### 2. Digital Signature

Ed25519 signature over the content hash using FactorTrace private key.

```
signature = Ed25519_sign(
  private_key,
  content_hash + report_id + tenant_id + generated_at
)
```

**Properties:**
- Proves FactorTrace generated the report
- Verifiable with public key (no API call needed)
- Non-repudiation

### 3. Timestamp Anchor (Optional)

External timestamp proof for legal disputes.

**Options:**
- RFC 3161 Timestamp Authority (traditional, widely accepted)
- OpenTimestamps (Bitcoin-anchored, free)
- Internal timestamp + signature (simplest, sufficient for most cases)

**Recommendation:** Start with internal timestamp + signature. Add RFC 3161 later if customers request it.

### 4. QR Code

Encodes verification URL for quick scanning.

```
QR payload: https://verify.factortrace.com/r/{report_id}
```

**Verification page shows:**
- Report metadata (company, date, total emissions)
- Hash verification status
- Signature verification status
- "VERIFIED" or "FAILED" badge

## Data Model Changes

### Report Model Additions

```python
class Report(Base):
    # ... existing fields ...

    # Verification fields
    content_hash: str        # SHA-256 hex (64 chars)
    signature: str           # Ed25519 signature (128 chars hex)
    signed_at: datetime      # When signature was created
    public_key_id: str       # Which key signed (for key rotation)

    # Optional external anchoring
    timestamp_token: str     # RFC 3161 token (nullable)
    timestamp_authority: str # TSA URL (nullable)
```

### New Table: SigningKeys

```python
class SigningKey(Base):
    __tablename__ = "signing_keys"

    id: str                  # e.g., "ft-2024-01"
    public_key: str          # Ed25519 public key (hex)
    created_at: datetime
    expires_at: datetime
    is_active: bool

    # Private key stored in secrets manager, NOT in DB
```

## API Endpoints

### Generate Signed Report

```
POST /api/v1/reports/{id}/sign
```

Called automatically after report generation. Adds hash + signature.

### Verify Report (Public)

```
GET /api/v1/verify/{report_id}

Response:
{
  "report_id": "abc123",
  "company_name": "Acme Corp",
  "generated_at": "2024-03-15T10:30:00Z",
  "total_tco2e": 1234.56,
  "hash_valid": true,
  "signature_valid": true,
  "public_key_id": "ft-2024-01",
  "status": "VERIFIED"
}
```

No authentication required - anyone can verify.

### Get Public Keys

```
GET /api/v1/verify/keys

Response:
{
  "keys": [
    {
      "id": "ft-2024-01",
      "public_key": "abc123...",
      "valid_from": "2024-01-01",
      "valid_until": "2025-01-01",
      "algorithm": "Ed25519"
    }
  ]
}
```

Enables offline verification.

## Security Considerations

### Key Management

| Concern | Mitigation |
|---------|------------|
| Private key exposure | Store in AWS Secrets Manager / HashiCorp Vault |
| Key rotation | Support multiple active keys, `public_key_id` in signature |
| Compromised key | Revocation list + new key issuance |
| Long-term validity | Keys valid 1 year, overlap during rotation |

### Attack Vectors

| Attack | Prevention |
|--------|------------|
| Hash collision | SHA-256 (256-bit security, collision-resistant) |
| Signature forgery | Ed25519 (128-bit security) |
| Replay attack | Include `report_id` + `generated_at` in signed data |
| Key substitution | Publish keys on website + in code |

## Integration Points

### PDF Generator

1. After emissions calculation complete
2. Generate canonical JSON of report data
3. Compute content_hash
4. Sign with Ed25519
5. Store hash + signature in Report model
6. Generate QR code pointing to verification URL
7. Embed QR in PDF footer

### Audit Log

All verification events logged:
- Report signed (who, when, key_id)
- Verification attempts (report_id, result, IP)
- Key rotation events

### iXBRL/XBRL Output

Include verification metadata as custom elements:
```xml
<ft:contentHash>abc123...</ft:contentHash>
<ft:signature>def456...</ft:signature>
<ft:verificationUrl>https://verify.factortrace.com/r/xyz</ft:verificationUrl>
```

## Implementation Phases

### Phase 1: Internal Signing (MVP)
- SHA-256 content hash
- Ed25519 signature
- Store in Report model
- Basic /verify endpoint

### Phase 2: QR + PDF Integration
- QR code generation
- Embed in PDF footer
- Public verification page (web)

### Phase 3: External Anchoring (If Requested)
- RFC 3161 timestamp authority integration
- OpenTimestamps (Bitcoin) option
- Enhanced audit logging

## Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1 | 4-6 hours |
| Phase 2 | 2-4 hours |
| Phase 3 | 8-12 hours |

## Dependencies

- `cryptography` library (Ed25519)
- `qrcode` library (QR generation)
- Secrets manager for key storage
- PDF generation service

## Open Questions

1. **Key storage:** AWS Secrets Manager vs HashiCorp Vault vs environment variables?
2. **Verification page:** Hosted on main domain or separate verify.factortrace.com?
3. **RFC 3161:** Which TSA? FreeTSA, DigiCert, or self-hosted?
4. **Offline verification:** Provide CLI tool for auditors?

## References

- [RFC 3161 - Time-Stamp Protocol](https://tools.ietf.org/html/rfc3161)
- [Ed25519 High-Speed Signatures](https://ed25519.cr.yp.to/)
- [OpenTimestamps](https://opentimestamps.org/)
- [ESRS Assurance Requirements](https://www.efrag.org/lab3)
