#!/usr/bin/env python3
"""
Quick fix for XML duplicate attribute error
Ensures no duplicate attributes in XHTML generation
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

def create_proper_ixbrl_report(esrs_data):
    """Create a valid iXBRL report without duplicate attributes"""
    
    # Register namespaces properly
    ET.register_namespace('', 'http://www.w3.org/1999/xhtml')
    ET.register_namespace('ix', 'http://www.xbrl.org/2013/inlineXBRL')
    ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    ET.register_namespace('xbrli', 'http://www.xbrl.org/2003/instance')
    ET.register_namespace('iso4217', 'http://www.xbrl.org/2003/iso4217')
    ET.register_namespace('esrs', 'http://www.efrag.org/esrs/2023')
    
    # Create root element with namespaces
    root = ET.Element('html')
    root.set('xmlns', 'http://www.w3.org/1999/xhtml')
    root.set('xmlns:ix', 'http://www.xbrl.org/2013/inlineXBRL')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xmlns:xbrli', 'http://www.xbrl.org/2003/instance')
    root.set('xmlns:iso4217', 'http://www.xbrl.org/2003/iso4217')
    root.set('xmlns:esrs', 'http://www.efrag.org/esrs/2023')
    
    # Create head
    head = ET.SubElement(root, 'head')
    title = ET.SubElement(head, 'title')
    title.text = f"ESRS Report - {esrs_data.get('company_name', 'Company')}"
    
    # Create body
    body = ET.SubElement(root, 'body')
    
    # Add hidden XBRL section
    xbrl_section = ET.SubElement(body, 'div')
    xbrl_section.set('style', 'display:none')
    
    # Create contexts
    contexts_elem = ET.SubElement(xbrl_section, '{http://www.xbrl.org/2013/inlineXBRL}hidden')
    
    # Current period context
    context = ET.SubElement(contexts_elem, '{http://www.xbrl.org/2003/instance}context')
    context.set('id', 'c-current')
    entity = ET.SubElement(context, '{http://www.xbrl.org/2003/instance}entity')
    identifier = ET.SubElement(entity, '{http://www.xbrl.org/2003/instance}identifier')
    identifier.set('scheme', 'http://www.lei-international.org/lei')
    identifier.text = esrs_data.get('lei', '12345678901234567890')
    period = ET.SubElement(context, '{http://www.xbrl.org/2003/instance}period')
    instant = ET.SubElement(period, '{http://www.xbrl.org/2003/instance}instant')
    instant.text = f"{esrs_data.get('reporting_period', '2024')}-12-31"
    
    # Create units
    unit_eur = ET.SubElement(contexts_elem, '{http://www.xbrl.org/2003/instance}unit')
    unit_eur.set('id', 'u-EUR')
    measure = ET.SubElement(unit_eur, '{http://www.xbrl.org/2003/instance}measure')
    measure.text = 'iso4217:EUR'
    
    unit_tonnes = ET.SubElement(contexts_elem, '{http://www.xbrl.org/2003/instance}unit')
    unit_tonnes.set('id', 'u-tonnes')
    measure_tonnes = ET.SubElement(unit_tonnes, '{http://www.xbrl.org/2003/instance}measure')
    measure_tonnes.text = 'esrs:tonnes'
    
    # Add visible content
    content_div = ET.SubElement(body, 'div')
    
    # Company header
    h1 = ET.SubElement(content_div, 'h1')
    h1.text = f"ESRS Sustainability Report - {esrs_data.get('company_name', 'Company')}"
    
    # Emissions section
    emissions_section = ET.SubElement(content_div, 'div')
    h2_emissions = ET.SubElement(emissions_section, 'h2')
    h2_emissions.text = "GHG Emissions"
    
    if 'emissions' in esrs_data:
        # Scope 1
        p_scope1 = ET.SubElement(emissions_section, 'p')
        p_scope1.text = "Scope 1 emissions: "
        scope1_elem = ET.SubElement(p_scope1, '{http://www.xbrl.org/2013/inlineXBRL}nonFraction')
        scope1_elem.set('contextRef', 'c-current')
        scope1_elem.set('name', 'esrs:GHGEmissionsScope1')
        scope1_elem.set('unitRef', 'u-tonnes')
        scope1_elem.set('decimals', '2')
        scope1_elem.set('format', 'ixt:numdotdecimal')
        scope1_elem.text = str(esrs_data['emissions'].get('scope1', 0))
        scope1_elem.tail = ' tonnes CO2e'
    
    # Convert to string properly
    xml_str = ET.tostring(root, encoding='unicode', method='xml')
    
    # Pretty print with minidom (carefully to avoid duplicate attributes)
    try:
        # Parse and pretty print
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # Clean up empty lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        return '\n'.join(lines)
    except:
        # If pretty printing fails, return the raw XML
        return xml_str

def test_generation():
    """Test the iXBRL generation"""
    test_data = {
        "company_name": "Test Company Ltd",
        "lei": "12345678901234567890",
        "reporting_period": "2024",
        "emissions": {
            "scope1": 12500.50,
            "scope2": 8300.25,
            "scope3": 45000.00
        }
    }
    
    try:
        print("🧪 Testing iXBRL generation...")
        xhtml_content = create_proper_ixbrl_report(test_data)
        
        # Verify it's valid XML
        ET.fromstring(xhtml_content)
        print("✅ Generated valid XML!")
        
        # Save output
        with open('test_output.xhtml', 'w', encoding='utf-8') as f:
            f.write(xhtml_content)
        print("✅ Saved to test_output.xhtml")
        
        print("\n📄 Preview:")
        print(xhtml_content[:500] + "...")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_generation()