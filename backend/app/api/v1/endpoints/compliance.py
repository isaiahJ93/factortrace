"""Compliance and iXBRL export endpoints"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

router = APIRouter()

def generate_ixbrl_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate iXBRL report for emissions data"""
    
    # Create the root XHTML element with iXBRL namespace
    root = ET.Element('html', {
        'xmlns': 'http://www.w3.org/1999/xhtml',
        'xmlns:ix': 'http://www.xbrl.org/2013/inlineXBRL',
        'xmlns:esrs': 'http://www.efrag.org/esrs/2023',
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    })
    
    # Head section
    head = ET.SubElement(root, 'head')
    title = ET.SubElement(head, 'title')
    title.text = f"Emissions Report - {data.get('reporting_period', datetime.now().year)}"
    
    # Body section
    body = ET.SubElement(root, 'body')
    
    # Header
    h1 = ET.SubElement(body, 'h1')
    h1.text = f"{data.get('organization', 'Organization')} - GHG Emissions Report"
    
    # Reporting period
    p_period = ET.SubElement(body, 'p')
    p_period.text = 'Reporting Period: '
    ix_period = ET.SubElement(p_period, '{http://www.xbrl.org/2013/inlineXBRL}nonNumeric', {
        'contextRef': 'period',
        'name': 'esrs:ReportingPeriod'
    })
    ix_period.text = str(data.get('reporting_period', datetime.now().year))
    
    # Emissions data section
    h2 = ET.SubElement(body, 'h2')
    h2.text = 'GHG Emissions by Scope'
    
    # Create table for emissions data
    table = ET.SubElement(body, 'table', {'border': '1'})
    
    # Table header
    thead = ET.SubElement(table, 'thead')
    tr_header = ET.SubElement(thead, 'tr')
    for header in ['Scope', 'Emissions (tCO2e)']:
        th = ET.SubElement(tr_header, 'th')
        th.text = header
    
    # Table body with iXBRL tags
    tbody = ET.SubElement(table, 'tbody')
    
    emissions = data.get('emissions', {})
    
    # Scope 1
    tr_scope1 = ET.SubElement(tbody, 'tr')
    td_label1 = ET.SubElement(tr_scope1, 'td')
    td_label1.text = 'Scope 1 - Direct Emissions'
    td_value1 = ET.SubElement(tr_scope1, 'td')
    ix_scope1 = ET.SubElement(td_value1, '{http://www.xbrl.org/2013/inlineXBRL}nonFraction', {
        'contextRef': 'period',
        'unitRef': 'tCO2e',
        'decimals': '2',
        'name': 'esrs:Scope1Emissions'
    })
    ix_scope1.text = str(emissions.get('scope1', 0))
    
    # Scope 2
    tr_scope2 = ET.SubElement(tbody, 'tr')
    td_label2 = ET.SubElement(tr_scope2, 'td')
    td_label2.text = 'Scope 2 - Indirect Emissions'
    td_value2 = ET.SubElement(tr_scope2, 'td')
    ix_scope2 = ET.SubElement(td_value2, '{http://www.xbrl.org/2013/inlineXBRL}nonFraction', {
        'contextRef': 'period',
        'unitRef': 'tCO2e',
        'decimals': '2',
        'name': 'esrs:Scope2Emissions'
    })
    ix_scope2.text = str(emissions.get('scope2', 0))
    
    # Scope 3
    tr_scope3 = ET.SubElement(tbody, 'tr')
    td_label3 = ET.SubElement(tr_scope3, 'td')
    td_label3.text = 'Scope 3 - Other Indirect Emissions'
    td_value3 = ET.SubElement(tr_scope3, 'td')
    ix_scope3 = ET.SubElement(td_value3, '{http://www.xbrl.org/2013/inlineXBRL}nonFraction', {
        'contextRef': 'period',
        'unitRef': 'tCO2e',
        'decimals': '2',
        'name': 'esrs:Scope3Emissions'
    })
    ix_scope3.text = str(emissions.get('scope3', 0))
    
    # Total
    tr_total = ET.SubElement(tbody, 'tr', {'style': 'font-weight: bold'})
    td_label_total = ET.SubElement(tr_total, 'td')
    td_label_total.text = 'Total Emissions'
    td_value_total = ET.SubElement(tr_total, 'td')
    total = emissions.get('scope1', 0) + emissions.get('scope2', 0) + emissions.get('scope3', 0)
    ix_total = ET.SubElement(td_value_total, '{http://www.xbrl.org/2013/inlineXBRL}nonFraction', {
        'contextRef': 'period',
        'unitRef': 'tCO2e',
        'decimals': '2',
        'name': 'esrs:TotalGHGEmissions'
    })
    ix_total.text = f"{total:.2f}"
    
    # Convert to string
    xml_str = ET.tostring(root, encoding='unicode', method='xml')
    
    # Pretty print
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    
    # Remove extra blank lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
    
    return {
        "format": "iXBRL",
        "standard": "ESRS E1-6",
        "content": pretty_xml,
        "filename": f"emissions_report_{data.get('reporting_period', datetime.now().year)}_ixbrl.html"
    }

@router.post("/export")
async def export_ixbrl(data: Dict[str, Any]):
    """Export emissions data as iXBRL report"""
    try:
        result = generate_ixbrl_report(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/standards")
async def list_supported_standards():
    """List supported reporting standards"""
    return {
        "standards": [
            {
                "code": "ESRS",
                "name": "European Sustainability Reporting Standards",
                "formats": ["iXBRL", "PDF", "CSV"]
            },
            {
                "code": "CDP",
                "name": "Carbon Disclosure Project",
                "formats": ["Excel", "CSV"]
            },
            {
                "code": "TCFD",
                "name": "Task Force on Climate-related Financial Disclosures",
                "formats": ["PDF", "JSON"]
            },
            {
                "code": "SBTi",
                "name": "Science Based Targets initiative",
                "formats": ["Excel", "CSV"]
            }
        ]
    }

@router.post("/validate")
async def validate_emissions_data(data: Dict[str, Any]):
    """Validate emissions data for compliance"""
    
    errors = []
    warnings = []
    
    # Check required fields
    if 'emissions' not in data:
        errors.append("Missing emissions data")
    else:
        emissions = data['emissions']
        if 'scope1' not in emissions:
            warnings.append("Scope 1 emissions not provided")
        if 'scope2' not in emissions:
            warnings.append("Scope 2 emissions not provided")
        if 'scope3' not in emissions:
            warnings.append("Scope 3 emissions recommended for full compliance")
    
    if 'reporting_period' not in data:
        errors.append("Reporting period is required")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "compliance_level": "Full" if len(errors) == 0 and len(warnings) == 0 else "Partial"
    }
