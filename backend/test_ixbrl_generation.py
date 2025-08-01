#!/usr/bin/env python3
"""
Test script to generate proper iXBRL and verify it works
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import json

def create_proper_ixbrl_report(data):
    """Generate a proper iXBRL report"""
    
    # Create root element with all required namespaces
    root = ET.Element('html', {
        'xmlns': 'http://www.w3.org/1999/xhtml',
        'xmlns:ix': 'http://www.xbrl.org/2013/inlineXBRL',
        'xmlns:xbrli': 'http://www.xbrl.org/2003/instance',
        'xmlns:xbrldi': 'http://xbrl.org/2006/xbrldi',
        'xmlns:iso4217': 'http://www.xbrl.org/2003/iso4217',
        'xmlns:esrs': 'http://www.efrag.org/esrs/2023',
        'xmlns:link': 'http://www.xbrl.org/2003/linkbase',
        'xmlns:xlink': 'http://www.w3.org/1999/xlink'
    })
    
    # Add head
    head = ET.SubElement(root, 'head')
    title = ET.SubElement(head, 'title')
    title.text = f"ESRS E1 Report - {data.get('entity', {}).get('name', 'Company')}"
    
    # Add meta tags
    ET.SubElement(head, 'meta', {'charset': 'UTF-8'})
    ET.SubElement(head, 'meta', {
        'name': 'description',
        'content': 'ESRS E1 Climate Change Disclosure - iXBRL Format'
    })
    
    # Add body
    body = ET.SubElement(root, 'body')
    
    # Add hidden section for contexts and units
    hidden = ET.SubElement(body, '{http://www.xbrl.org/2013/inlineXBRL}hidden')
    
    # Add contexts
    contexts = ET.SubElement(hidden, '{http://www.xbrl.org/2013/inlineXBRL}resources')
    
    # Current period context
    ctx_current = ET.SubElement(contexts, '{http://www.xbrl.org/2003/instance}context', {'id': 'current-period'})
    entity_current = ET.SubElement(ctx_current, '{http://www.xbrl.org/2003/instance}entity')
    identifier_current = ET.SubElement(entity_current, '{http://www.xbrl.org/2003/instance}identifier', {
        'scheme': 'http://standards.iso.org/iso/17442'
    })
    identifier_current.text = data.get('entity', {}).get('lei', 'PENDING00000000000000')
    
    period_current = ET.SubElement(ctx_current, '{http://www.xbrl.org/2003/instance}period')
    start_date = ET.SubElement(period_current, '{http://www.xbrl.org/2003/instance}startDate')
    start_date.text = data.get('period', {}).get('start_date', '2024-01-01')
    end_date = ET.SubElement(period_current, '{http://www.xbrl.org/2003/instance}endDate')
    end_date.text = data.get('period', {}).get('end_date', '2024-12-31')
    
    # Add units
    units = ET.SubElement(hidden, '{http://www.xbrl.org/2013/inlineXBRL}resources')
    
    # tCO2e unit
    unit_tco2e = ET.SubElement(units, '{http://www.xbrl.org/2003/instance}unit', {'id': 'u-tCO2e'})
    measure_tco2e = ET.SubElement(unit_tco2e, '{http://www.xbrl.org/2003/instance}measure')
    measure_tco2e.text = 'esrs:tonnesCO2e'
    
    # EUR unit
    unit_eur = ET.SubElement(units, '{http://www.xbrl.org/2003/instance}unit', {'id': 'u-EUR'})
    measure_eur = ET.SubElement(unit_eur, '{http://www.xbrl.org/2003/instance}measure')
    measure_eur.text = 'iso4217:EUR'
    
    # Add visible content
    main_content = ET.SubElement(body, 'div', {'class': 'main-content'})
    
    # Title section
    h1 = ET.SubElement(main_content, 'h1')
    h1.text = 'ESRS E1 Climate-related Disclosures'
    
    # Entity information
    entity_section = ET.SubElement(main_content, 'section', {'class': 'entity-info'})
    h2_entity = ET.SubElement(entity_section, 'h2')
    h2_entity.text = 'Reporting Entity'
    
    p_entity = ET.SubElement(entity_section, 'p')
    p_entity.text = 'Entity: '
    # Proper iXBRL text fact
    entity_name_elem = ET.SubElement(p_entity, '{http://www.xbrl.org/2013/inlineXBRL}nonNumeric', {
        'name': 'esrs:EntityName',
        'contextRef': 'current-period'
    })
    entity_name_elem.text = data.get('entity', {}).get('name', 'Test Company')
    
    # GHG Emissions section
    emissions_section = ET.SubElement(main_content, 'section', {'class': 'ghg-emissions'})
    h2_emissions = ET.SubElement(emissions_section, 'h2')
    h2_emissions.text = 'GHG Emissions (E1-6)'
    
    # Create table
    table = ET.SubElement(emissions_section, 'table', {'class': 'emissions-table'})
    tbody = ET.SubElement(table, 'tbody')
    
    # Get emissions data
    ghg_data = data.get('climate_change', {}).get('ghg_emissions', {})
    
    # Scope 1
    tr1 = ET.SubElement(tbody, 'tr')
    td1_label = ET.SubElement(tr1, 'td')
    td1_label.text = 'Scope 1 Emissions: '
    td1_value = ET.SubElement(tr1, 'td', {'class': 'numeric'})
    
    # Proper iXBRL numeric fact
    scope1_elem = ET.SubElement(td1_value, '{http://www.xbrl.org/2013/inlineXBRL}nonFraction', {
        'name': 'esrs:Scope1Emissions',
        'contextRef': 'current-period',
        'unitRef': 'u-tCO2e',
        'decimals': '0'
    })
    scope1_value = ghg_data.get('scope1_total', 0)
    scope1_elem.text = f"{scope1_value:,.0f}"
    
    td1_unit = ET.SubElement(tr1, 'td')
    td1_unit.text = ' tCO₂e'
    
    # Scope 2 Location-based
    tr2 = ET.SubElement(tbody, 'tr')
    td2_label = ET.SubElement(tr2, 'td')
    td2_label.text = 'Scope 2 (Location-based): '
    td2_value = ET.SubElement(tr2, 'td', {'class': 'numeric'})
    
    scope2_elem = ET.SubElement(td2_value, '{http://www.xbrl.org/2013/inlineXBRL}nonFraction', {
        'name': 'esrs:Scope2LocationBased',
        'contextRef': 'current-period',
        'unitRef': 'u-tCO2e',
        'decimals': '0'
    })
    scope2_value = ghg_data.get('scope2_location', 0)
    scope2_elem.text = f"{scope2_value:,.0f}"
    
    td2_unit = ET.SubElement(tr2, 'td')
    td2_unit.text = ' tCO₂e'
    
    # Scope 3
    tr3 = ET.SubElement(tbody, 'tr')
    td3_label = ET.SubElement(tr3, 'td')
    td3_label.text = 'Scope 3 Emissions: '
    td3_value = ET.SubElement(tr3, 'td', {'class': 'numeric'})
    
    scope3_elem = ET.SubElement(td3_value, '{http://www.xbrl.org/2013/inlineXBRL}nonFraction', {
        'name': 'esrs:Scope3Emissions',
        'contextRef': 'current-period',
        'unitRef': 'u-tCO2e',
        'decimals': '0'
    })
    scope3_value = ghg_data.get('scope3_total', 0)
    scope3_elem.text = f"{scope3_value:,.0f}"
    
    td3_unit = ET.SubElement(tr3, 'td')
    td3_unit.text = ' tCO₂e'
    
    # Total
    tr_total = ET.SubElement(tbody, 'tr', {'class': 'total'})
    td_total_label = ET.SubElement(tr_total, 'td')
    td_total_label.text = 'Total GHG Emissions: '
    td_total_value = ET.SubElement(tr_total, 'td', {'class': 'numeric total'})
    
    total_elem = ET.SubElement(td_total_value, '{http://www.xbrl.org/2013/inlineXBRL}nonFraction', {
        'name': 'esrs:TotalGHGEmissions',
        'contextRef': 'current-period',
        'unitRef': 'u-tCO2e',
        'decimals': '0'
    })
    total_value = ghg_data.get('total_ghg_emissions', 0)
    total_elem.text = f"{total_value:,.0f}"
    
    td_total_unit = ET.SubElement(tr_total, 'td')
    td_total_unit.text = ' tCO₂e'
    
    # Convert to string with proper formatting
    ET.register_namespace('', 'http://www.w3.org/1999/xhtml')
    ET.register_namespace('ix', 'http://www.xbrl.org/2013/inlineXBRL')
    ET.register_namespace('xbrli', 'http://www.xbrl.org/2003/instance')
    ET.register_namespace('iso4217', 'http://www.xbrl.org/2003/iso4217')
    ET.register_namespace('esrs', 'http://www.efrag.org/esrs/2023')
    
    # Get string representation
    xml_str = ET.tostring(root, encoding='unicode')
    
    # Pretty print with minidom
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Clean up the output
    lines = pretty_xml.split('\n')
    # Remove the XML declaration as we want HTML
    if lines[0].startswith('<?xml'):
        lines = lines[1:]
    
    # Add DOCTYPE
    final_output = '<!DOCTYPE html>\n' + '\n'.join(lines)
    
    return final_output

def test_generation():
    """Test the iXBRL generation"""
    
    # Sample data
    test_data = {
        "entity": {
            "name": "Test Company Ltd",
            "lei": "12345678901234567890"
        },
        "period": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        },
        "climate_change": {
            "ghg_emissions": {
                "scope1_total": 1500,
                "scope2_location": 800,
                "scope2_market": 600,
                "scope3_total": 5000,
                "total_ghg_emissions": 7300
            }
        }
    }
    
    # Generate the report
    xhtml_content = create_proper_ixbrl_report(test_data)
    
    # Save to file
    with open('test_ixbrl_output.xhtml', 'w', encoding='utf-8') as f:
        f.write(xhtml_content)
    
    print("✅ Generated test_ixbrl_output.xhtml")
    
    # Verify it contains iXBRL tags
    if '<ix:nonFraction' in xhtml_content:
        print("✅ Contains ix:nonFraction tags")
    else:
        print("❌ Missing ix:nonFraction tags")
    
    if '<ix:nonNumeric' in xhtml_content:
        print("✅ Contains ix:nonNumeric tags")
    else:
        print("❌ Missing ix:nonNumeric tags")
    
    if 'contextRef=' in xhtml_content:
        print("✅ Contains contextRef attributes")
    else:
        print("❌ Missing contextRef attributes")
    
    if 'unitRef=' in xhtml_content:
        print("✅ Contains unitRef attributes")
    else:
        print("❌ Missing unitRef attributes")
    
    # Count facts
    import re
    fractions = len(re.findall(r'<ix:nonFraction', xhtml_content))
    numerics = len(re.findall(r'<ix:nonNumeric', xhtml_content))
    print(f"\n📊 Fact counts:")
    print(f"  Numeric facts: {fractions}")
    print(f"  Text facts: {numerics}")
    
    return xhtml_content

if __name__ == "__main__":
    test_generation()
    print("\n🔍 Now run: python3 verify_ixbrl.py test_ixbrl_output.xhtml")