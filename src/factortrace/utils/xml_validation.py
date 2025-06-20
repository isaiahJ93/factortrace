from __future__ import annotations
from xmlschema import XMLSchema
from typing import Tuple, List
def validate_vsme_xml(xml_string: str):
    return True, []

def add_to_xml_method(cls):
    """Stub decorator until logic is implemented."""
    return cls

VSME_SCHEMA_PATH = "schemas/vsme/vsme-all.xsd"

def validate_vsme_xml(xml_string: str) -> Tuple[bool, List[str]]:
    """
    Validate the given XML string against the VSME XBRL schema.
    Returns:
        (is_valid: bool, errors: list of str)
    """
    try:
        schema = XMLSchema(VSME_SCHEMA_PATH)
        is_valid = schema.is_valid(xml_string)
        errors = [str(e) for e in schema.validate(xml_string)] if not is_valid else []
        return is_valid, errors
    except Exception as e:
        return False, [f"Schema load or validation error: {e}"]
    