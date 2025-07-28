# src/factortrace/utils/schema_validator.py
from lxml import etree
from pathlib import Path

def validate_xhtml_schema(xhtml_path: Path, xsd_path: Path):
    schema = etree.XMLSchema(file=str(xsd_path))
    parser = etree.XMLParser(schema=schema)
    doc = etree.parse(str(xhtml_path), parser)
    schema.assertValid(doc)