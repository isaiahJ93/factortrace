from xmlschema import XMLSchema
from factortrace.models.emissions_voucher import EmissionVoucher
from tests.data.sample_data import SAMPLE_DATA

def validate_vsme_export(xml_string: str) -> None:
    """
    Validate your exported XML against EFRAG's VSME XBRL taxonomy.
    """
    xsd_path = "schemas/vsme/vsme-all.xsd"
    schema = XMLSchema(xsd_path)

    if schema.is_valid(xml_string):
        print("✅ XML is valid against VSME taxonomy")
    else:
        print("❌ XML is NOT valid:")
        errors = schema.validate(xml_string)
        for e in errors:
            print("-", e)

def test_emission_voucher_vsme_compliance():
    voucher = EmissionVoucher(**SAMPLE_DATA)
    xml_string = voucher.to_xml()
    validate_vsme_export(xml_string)

    from xmlschema import XMLSchema

def test_vsme_schema_validation():
    voucher = EmissionVoucher(**SAMPLE_DATA)
    xml_string = voucher.to_xml()

    schema = XMLSchema("schemas/vsme/vsme-all.xsd")
    assert schema.is_valid(xml_string), "❌ VSME XML is not schema-valid"