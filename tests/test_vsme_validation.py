import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))


def test_vsme_schema_validation():
    from factortrace.models.emissions_voucher import EmissionVoucher
    from factortrace.utils.xml_validation import validate_vsme_xml
    from tests.data.voucher_sample import SAMPLE_DATA
    from tests.data.sample_data import SAMPLE_DATA

    voucher = EmissionVoucher(**SAMPLE_DATA)
    xml_string = voucher.to_xml()
    is_valid, errors = validate_vsme_xml(xml_string)

    assert is_valid, f"Schema validation failed: {errors}"

