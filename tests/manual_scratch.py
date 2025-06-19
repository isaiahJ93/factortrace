from core.voucher_generator import generate_voucher

sample = {
    "supplier_id": "SUP-001",
    "supplier_name": "Acme Metals",
    "legal_entity_identifier": "5493001KJTIIGC8Y1R12",
    "product_category": "Materials",
    "cost": 1200.0,
    "material_type": "Steel",
    "origin_country": "DE",
}

print(generate_voucher(sample))
