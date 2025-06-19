"""
Serialize a Scope-3 voucher (dict or dataclass) to XML and validate
it against resources/schema/voucher.xsd.  Only lxml is required.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List
from enum import Enum
from lxml import etree
from lxml.etree import Element, QName, SubElement, tostring

# --------------------------------------------------------------------------- #
# Constants – these MUST match voucher.xsd                                    #
# --------------------------------------------------------------------------- #

NAMESPACE: str = "https://scope3.dev/voucher/2025-06"
NSMAP = {None: NAMESPACE}                     # default namespace

FIELD_ORDER: List[str] = [
    "supplier_id",
    "supplier_name",
    "legal_entity_identifier",
    "tier",
    "product_category",
    "cost",
    "material_type",
    "origin_country",
    "emission_factor",
    "fallback_factor_used",
    "total_co2e",
    "submission_date",
    "voucher_uuid",
    "hash",
]

# --------------------------------------------------------------------------- #
# Public helpers                                                              #
# --------------------------------------------------------------------------- #


def serialize_voucher(voucher: Any) -> str:
    """Return pretty-printed XML for *voucher* (dict OR dataclass)."""

    # normalise input --------------------------------------------------------
    if is_dataclass(voucher):
        data: Dict[str, Any] = asdict(voucher)
    elif isinstance(voucher, dict):
        data = dict(voucher)
    else:
        raise TypeError("voucher must be a dict or dataclass")

    # build XML --------------------------------------------------------------
    root = Element(QName(NAMESPACE, "voucher"), nsmap=NSMAP)

    for field in FIELD_ORDER:
        if field not in data:
            raise KeyError(f"voucher missing {field!r}")
        val = data[field]

        elem = SubElement(root, QName(NAMESPACE, field))
        elem.text = "true" if val is True else "false" if val is False else str(val)

    xml_bytes = tostring(
        root, pretty_print=True, xml_declaration=True, encoding="UTF-8"
    )
    return xml_bytes.decode()


def validate_xml(xml: str | bytes, xsd_path: str | Path) -> bool:
    """Validate *xml* against *xsd_path*.  Return ``True`` if valid."""
    if isinstance(xsd_path, Path):
        xsd_path = str(xsd_path)

    if isinstance(xml, str):
        xml = xml.encode()

    schema = etree.XMLSchema(etree.parse(xsd_path))
    return schema.validate(etree.fromstring(xml))


# --------------------------------------------------------------------------- #
# Quick CLI helper:  python -m core.voucher_xml_serializer foo.json           #
# --------------------------------------------------------------------------- #

if __name__ == "__main__":  # pragma: no cover
    import json, sys

    if len(sys.argv) != 2:
        sys.exit("usage: python -m core.voucher_xml_serializer <voucher.json>")

    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    xml_out = serialize_voucher(payload)
    print(xml_out)

    xsd_file = (
        Path(__file__).resolve().parent.parent
        / "resources"
        / "schema"
        / "voucher.xsd"
    )

    ok = validate_xml(xml_out, xsd_file)
    print("✔ valid" if ok else "✖ invalid")
    sys.exit(0 if ok else 1)