from enum import Enum

"""
Smoke-test: generator ➜ serializer ➜ XSD validator.
Run with:  PYTHONPATH=src pytest -q
"""

from pathlib import Path
from api.schemas import VoucherInput
from generator.voucher_generator import generate_voucher
from factortrace.voucher_xml_serializer import serialize_voucher, validate_xml  # ✅


def test_voucher_xml_is_valid() -> None:
    sample = {
         "supplier_id": "SUP-001",
         "supplier_name": "Acme Metals",
         "legal_entity_identifier": "5493001KTIIIGC8YR1212",
         "product_category": "Materials",
         "cost": 1200.0,
         "material_type": "Steel",
         "product_cn_code": "7208.39.00",
         "origin_country": "DE",
         "emissions_factor": 2.5,
         "emissions_factor_id": "EF-001", 
         "fallback_factor_used": False,
}

    generate_voucher(VoucherInput(**sample))     # adds CO2e, uuid, hash, etc.
    xml_str = serialize_voucher(voucher)

    xsd_file = Path("src/resources/schema/voucher.xsd").resolve()
    assert validate_xml(xml_str, xsd_file), "XML failed XSD validation"
    
    import sys, json
if __name__ == "__main__" and len(sys.argv) > 1:
    json_path = sys.argv[1]
    with open(json_path, "r") as f:
        data = json.load(f)
    from core.voucher_generator import generate_voucher
    voucher = generate_voucher(data)
    xml = serialize_voucher(voucher)
    print(xml)

    # Validate XML
    xsd_path = "src/resources/schema/voucher.xsd"
    if validate_xml(xml, xsd_path):
        print("✅ Valid XML!")
    else:
        print("❌ Invalid XML.")
