# src/app/utils/xml_utils.py

from pathlib import Path
import xmlschema

XSD_PATH = Path(__file__).resolve().parent.parent / "xsd" / "voucher.xsd"
schema = xmlschema.XMLSchema11(XSD_PATH)
