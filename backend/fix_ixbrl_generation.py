#!/usr/bin/env python3
"""
Fix iXBRL generation by adding proper tagging functions
This should be integrated into your esrs_e1_full.py
"""

import xml.etree.ElementTree as ET
from html import escape
from typing import Optional, Union, Dict, Any
from decimal import Decimal
import re

# XML Special character escaping for XBRL compliance
def escape_xbrl_string(value: Any) -> str:
    """Escape string for XBRL/XML compliance"""
    if value is None:
        return ""
    
    # Convert to string first
    text = str(value)
    
    # XML escape (handles &, <, >, ", ')
    text = escape(text, quote=True)
    
    # Additional XBRL-specific escaping
    # Remove control characters that are invalid in XML
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    return text

def create_ix_nonfraction(
    parent: ET.Element,
    name: str,
    value: Union[int, float, Decimal],
    context_ref: str,
    unit_ref: str,
    decimals: str = "0",
    scale: Optional[str] = None,
    format_string: Optional[str] = None
) -> ET.Element:
    """
    Create an ix:nonFraction element for numeric facts
    
    Args:
        parent: Parent element to append to
        name: XBRL concept name (e.g., "esrs:Scope1Emissions")
        value: Numeric value
        context_ref: Context reference ID
        unit_ref: Unit reference ID
        decimals: Decimal precision (default "0")
        scale: Scale factor (e.g., "6" for millions)
        format_string: iXBRL format string
    """
    attribs = {
        "name": name,
        "contextRef": context_ref,
        "unitRef": unit_ref,
        "decimals": decimals
    }
    
    if scale:
        attribs["scale"] = scale
    
    if format_string:
        attribs["format"] = format_string
    
    # Create the element
    elem = ET.SubElement(parent, "{http://www.xbrl.org/2013/inlineXBRL}nonFraction", attribs)
    
    # Format the value for display
    if isinstance(value, (int, Decimal)):
        elem.text = f"{value:,}"  # Add thousand separators
    else:
        elem.text = f"{value:,.2f}"  # Two decimal places with separators
    
    return elem

def create_ix_nonnumeric(
    parent: ET.Element,
    name: str,
    value: str,
    context_ref: str,
    escape_html: bool = True
) -> ET.Element:
    """
    Create an ix:nonNumeric element for text facts
    
    Args:
        parent: Parent element to append to
        name: XBRL concept name
        value: Text value
        context_ref: Context reference ID
        escape_html: Whether to escape HTML characters
    """
    attribs = {
        "name": name,
        "contextRef": context_ref
    }
    
    elem = ET.SubElement(parent, "{http://www.xbrl.org/2013/inlineXBRL}nonNumeric", attribs)
    elem.text = escape_xbrl_string(value) if escape_html else value
    
    return elem

def create_ix_continuation(
    parent: ET.Element,
    continued_at: str,
    id: Optional[str] = None
) -> ET.Element:
    """Create an ix:continuation element for multi-part facts"""
    attribs = {"continuedAt": continued_at}
    if id:
        attribs["id"] = id
    
    return ET.SubElement(parent, "{http://www.xbrl.org/2013/inlineXBRL}continuation", attribs)

def create_ix_exclude(parent: ET.Element) -> ET.Element:
    """Create an ix:exclude element for excluded content"""
    return ET.SubElement(parent, "{http://www.xbrl.org/2013/inlineXBRL}exclude")

def create_ix_footnote(
    parent: ET.Element,
    footnote_id: str,
    footnote_role: str = "http://www.xbrl.org/2003/role/footnote",
    fact_refs: Optional[list] = None
) -> ET.Element:
    """Create an ix:footnote element"""
    attribs = {
        "id": footnote_id,
        "footnoteRole": footnote_role
    }
    
    if fact_refs:
        attribs["factRefs"] = " ".join(fact_refs)
    
    return ET.SubElement(parent, "{http://www.xbrl.org/2013/inlineXBRL}footnote", attribs)

def add_ghg_emissions_facts(
    parent: ET.Element,
    emissions_data: Dict[str, Any],
    context_ref: str = "current-period"
) -> None:
    """
    Add GHG emissions facts with proper iXBRL tagging
    
    Args:
        parent: Parent element (typically a div or section)
        emissions_data: Dictionary with emission values
        context_ref: Context reference for the facts
    """
    # Create a section for emissions
    section = ET.SubElement(parent, "section", {"class": "ghg-emissions"})
    
    # Add heading
    h2 = ET.SubElement(section, "h2")
    h2.text = "GHG Emissions (E1-6)"
    
    # Create table for emissions data
    table = ET.SubElement(section, "table", {"class": "emissions-table"})
    tbody = ET.SubElement(table, "tbody")
    
    # Scope 1 Emissions
    tr1 = ET.SubElement(tbody, "tr")
    td1_label = ET.SubElement(tr1, "td")
    td1_label.text = "Scope 1 (Direct Emissions):"
    td1_value = ET.SubElement(tr1, "td", {"class": "numeric"})
    create_ix_nonfraction(
        td1_value,
        "esrs:Scope1Emissions",
        emissions_data.get("scope1_total", 0),
        context_ref,
        "u-tCO2e",
        decimals="0"
    )
    td1_unit = ET.SubElement(tr1, "td")
    td1_unit.text = " tCO₂e"
    
    # Scope 2 Emissions (Location-based)
    tr2 = ET.SubElement(tbody, "tr")
    td2_label = ET.SubElement(tr2, "td")
    td2_label.text = "Scope 2 (Location-based):"
    td2_value = ET.SubElement(tr2, "td", {"class": "numeric"})
    create_ix_nonfraction(
        td2_value,
        "esrs:Scope2LocationBased",
        emissions_data.get("scope2_location", 0),
        context_ref,
        "u-tCO2e",
        decimals="0"
    )
    td2_unit = ET.SubElement(tr2, "td")
    td2_unit.text = " tCO₂e"
    
    # Scope 2 Emissions (Market-based)
    tr2m = ET.SubElement(tbody, "tr")
    td2m_label = ET.SubElement(tr2m, "td")
    td2m_label.text = "Scope 2 (Market-based):"
    td2m_value = ET.SubElement(tr2m, "td", {"class": "numeric"})
    create_ix_nonfraction(
        td2m_value,
        "esrs:Scope2MarketBased",
        emissions_data.get("scope2_market", 0),
        context_ref,
        "u-tCO2e",
        decimals="0"
    )
    td2m_unit = ET.SubElement(tr2m, "td")
    td2m_unit.text = " tCO₂e"
    
    # Scope 3 Emissions
    tr3 = ET.SubElement(tbody, "tr")
    td3_label = ET.SubElement(tr3, "td")
    td3_label.text = "Scope 3 (Value Chain):"
    td3_value = ET.SubElement(tr3, "td", {"class": "numeric"})
    create_ix_nonfraction(
        td3_value,
        "esrs:Scope3Emissions",
        emissions_data.get("scope3_total", 0),
        context_ref,
        "u-tCO2e",
        decimals="0"
    )
    td3_unit = ET.SubElement(tr3, "td")
    td3_unit.text = " tCO₂e"
    
    # Total Emissions
    tr_total = ET.SubElement(tbody, "tr", {"class": "total-row"})
    td_total_label = ET.SubElement(tr_total, "td")
    td_total_label.text = "Total GHG Emissions:"
    td_total_value = ET.SubElement(tr_total, "td", {"class": "numeric total"})
    create_ix_nonfraction(
        td_total_value,
        "esrs:TotalGHGEmissions",
        emissions_data.get("total_ghg_emissions", 0),
        context_ref,
        "u-tCO2e",
        decimals="0"
    )
    td_total_unit = ET.SubElement(tr_total, "td")
    td_total_unit.text = " tCO₂e"

def add_entity_information(
    parent: ET.Element,
    entity_data: Dict[str, Any],
    context_ref: str = "current-instant"
) -> None:
    """Add entity information with proper iXBRL tagging"""
    section = ET.SubElement(parent, "section", {"class": "entity-information"})
    
    # Entity Name
    p_name = ET.SubElement(section, "p")
    p_name.text = "Entity Name: "
    create_ix_nonnumeric(
        p_name,
        "esrs:EntityName",
        entity_data.get("name", ""),
        context_ref
    )
    
    # LEI
    p_lei = ET.SubElement(section, "p")
    p_lei.text = "LEI: "
    create_ix_nonnumeric(
        p_lei,
        "esrs:LegalEntityIdentifier",
        entity_data.get("lei", ""),
        context_ref
    )
    
    # NACE Code
    p_nace = ET.SubElement(section, "p")
    p_nace.text = "Primary NACE Code: "
    create_ix_nonnumeric(
        p_nace,
        "esrs:PrimaryNaceCode",
        entity_data.get("primary_nace_code", ""),
        context_ref
    )

# Integration function to patch existing implementation
def enhance_ixbrl_output(root_element: ET.Element, data: Dict[str, Any]) -> None:
    """
    Enhance existing XHTML with proper iXBRL tags
    This function should be called after basic XHTML structure is created
    """
    # Find or create body element
    body = root_element.find(".//{http://www.w3.org/1999/xhtml}body")
    if body is None:
        body = root_element.find(".//body")
    
    if body is None:
        raise ValueError("No body element found in XHTML structure")
    
    # Add entity information
    if "entity" in data:
        add_entity_information(body, data["entity"])
    
    # Add GHG emissions
    if "climate_change" in data and "ghg_emissions" in data["climate_change"]:
        add_ghg_emissions_facts(body, data["climate_change"]["ghg_emissions"])
    
    # Add more sections as needed...

if __name__ == "__main__":
    # Test the functions
    test_data = {
        "entity": {
            "name": "Test Company Ltd",
            "lei": "12345678901234567890",
            "primary_nace_code": "62.01"
        },
        "climate_change": {
            "ghg_emissions": {
                "scope1_total": 1500.5,
                "scope2_location": 800.0,
                "scope2_market": 600.0,
                "scope3_total": 5000.0,
                "total_ghg_emissions": 7300.5
            }
        }
    }
    
    # Create test structure
    root = ET.Element("html", {
        "xmlns": "http://www.w3.org/1999/xhtml",
        "xmlns:ix": "http://www.xbrl.org/2013/inlineXBRL",
        "xmlns:xbrli": "http://www.xbrl.org/2003/instance",
        "xmlns:esrs": "http://www.efrag.org/esrs/2023"
    })
    
    body = ET.SubElement(root, "body")
    enhance_ixbrl_output(root, test_data)
    
    # Pretty print
    from xml.dom import minidom
    xml_str = ET.tostring(root, encoding='unicode')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    print("Sample iXBRL output:")
    print(pretty_xml)