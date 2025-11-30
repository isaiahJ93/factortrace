






Voucher/Credit Purchase API Contract



Contract-first spec for purchasing and redeeming vouchers/credits.









POST /api/v1/vouchers/purchase



Purpose

Allow a buyer (or supplier) to purchase a pack of credits/vouchers.



Request Body (JSON)



Required:





pack_type (string): e.g. "SINGLE_REPORT", "BUNDLE_10", "BUNDLE_50".

quantity (int): Number of vouchers in this purchase (for bulk packs).

buyer_email (string): Email to send voucher codes to.

currency (string): ISO 4217 (e.g. "EUR").

payment_reference (string): Reference from payment provider (Stripe, etc.).



Optional:





buyer_name (string)

notes (string)



Business Rules





Price must be calculated server-side based on pack_type, quantity, and current pricing model.

tenant_id is derived from the authenticated buyer’s organisation.

One or more voucher codes are generated and persisted with:



code (secure random string).

tenant_id.

status = "UNUSED".

credits (e.g. number of reports allowed).

Email(s) must be queued/sent with voucher codes to buyer_email.



Success Response (201)



{

  "purchase_id": "uuid",

  "tenant_id": "tenant_abc",

  "pack_type": "BUNDLE_10",

  "quantity": 10,

  "currency": "EUR",

  "total_amount": 9500,

  "vouchers": [

    {

      "code": "FT-ABC123-XYZ",

      "status": "UNUSED",

      "credits": 1

    }

  ],

  "created_at": "2024-11-30T10:00:00Z"

}







POST /api/v1/vouchers/redeem



Purpose

Allow a supplier to redeem a voucher code to gain access to FactorTrace (credits/reports).



Request Body (JSON)



Required:





code (string): Voucher code received via email.

email (string): Supplier contact email.

company_name (string): Supplier organisation.



Optional:





name (string): Contact person name.



Business Rules





Find voucher by code:



If not found → 404.

If already used / expired → 400 with clear error.

Link voucher to a supplier tenant:



If tenant exists for this company → link.

Else create a new tenant (Tier 1/2 supplier) and link voucher.

Mark voucher as:



status = "USED".

Store redeemed_at, redeemed_by_email.

Issue auth credentials / session for supplier so they can:



Upload data.

Use credits to generate reports.



Success Response (200)



{

  "tenant_id": "tenant_supplier_123",

  "voucher_code": "FT-ABC123-XYZ",

  "credits_remaining": 1,

  "access_token": "jwt-or-session-token",

  "consumed": true

}

Error Responses



400 Bad Request:



{

  "detail": [

    {

      "field": "code",

      "message": "Voucher has already been used or is expired."

    }

  ]

}

404 Not Found – unknown voucher code.









GET /api/v1/vouchers



Purpose

List vouchers for the current tenant (buyers).



Business Rules





Tenant-scoped.

Paginated.

No exposure of voucher codes from other tenants.







Tests Required



Successful purchase flow (vouchers created, email queued).

Successful redeem flow (voucher → tenant link, status change).

Double redeem attempt fails with 400.

Cross-tenant voucher access blocked.

Edge cases: invalid code, expired code, wrong email (if enforced).

