from lxml import etree
import json
from datetime import datetime

class XBRLService:
    async def generate_xbrl(self, data, format="ixbrl"):
        """Generate XBRL/iXBRL document"""
        
        # Create XBRL instance document
        xbrl_ns = "http://www.xbrl.org/2003/instance"
        esrs_ns = "http://xbrl.efrag.org/taxonomy/2023-12-31/esrs"
        
        root = etree.Element(
            "{%s}xbrl" % xbrl_ns,
            nsmap={
                None: xbrl_ns,
                "esrs": esrs_ns,
                "iso4217": "http://www.xbrl.org/2003/iso4217"
            }
        )
        
        # Add context
        context = etree.SubElement(root, "context", id="c1")
        entity = etree.SubElement(context, "entity")
        etree.SubElement(entity, "identifier", scheme="http://www.gleif.org").text = data.lei
        
        period = etree.SubElement(context, "period")
        if data.reporting_period == "FY":
            etree.SubElement(period, "startDate").text = f"{data.reporting_year}-01-01"
            etree.SubElement(period, "endDate").text = f"{data.reporting_year}-12-31"
        else:
            # Quarter logic
            quarter_map = {"Q1": ("01-01", "03-31"), "Q2": ("04-01", "06-30"), 
                          "Q3": ("07-01", "09-30"), "Q4": ("10-01", "12-31")}
            start, end = quarter_map[data.reporting_period]
            etree.SubElement(period, "startDate").text = f"{data.reporting_year}-{start}"
            etree.SubElement(period, "endDate").text = f"{data.reporting_year}-{end}"
        
        # Add units
        unit_co2 = etree.SubElement(root, "unit", id="tCO2e")
        etree.SubElement(unit_co2, "measure").text = "esrs:tCO2e"
        
        # Add facts
        facts = [
            ("esrs:Scope1GHGEmissions", str(data.scope1.value), "tCO2e"),
            ("esrs:Scope2GHGEmissions", str(data.scope2.value), "tCO2e"),
            ("esrs:Scope3GHGEmissions", str(data.scope3.value), "tCO2e"),
            ("esrs:TotalGHGEmissions", str(data.scope1.value + data.scope2.value + data.scope3.value), "tCO2e")
        ]
        
        for concept, value, unit in facts:
            fact = etree.SubElement(
                root, 
                concept.split(":")[1],
                contextRef="c1",
                unitRef=unit,
                decimals="2"
            )
            fact.text = value
        
        # Convert to string
        xbrl_string = etree.tostring(root, pretty_print=True, encoding="UTF-8", xml_declaration=True)
        
        if format == "ixbrl":
            # Wrap in HTML for inline XBRL
            return self._create_ixbrl_document(xbrl_string, data)
        
        return xbrl_string.decode('utf-8')
    
    def _create_ixbrl_document(self, xbrl_content, data):
        """Create inline XBRL (iXBRL) HTML document"""
        html = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
<head>
    <title>Emissions Report - {data.company_name}</title>
    <meta charset="UTF-8"/>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 8px; }}
        .emissions-table {{ width: 100%; margin-top: 20px; border-collapse: collapse; }}
        .emissions-table th, .emissions-table td {{ border: 1px solid #ddd; padding: 12px; text-align: right; }}
        .emissions-table th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{data.company_name}</h1>
        <p>Emissions Report - {data.reporting_period} {data.reporting_year}</p>
        <p>Standard: {data.standard}</p>
    </div>
    
    <table class="emissions-table">
        <tr>
            <th>Emission Scope</th>
            <th>Value (tCO₂e)</th>
            <th>Data Quality</th>
        </tr>
        <tr>
            <td>Scope 1 - Direct Emissions</td>
            <td><ix:nonFraction contextRef="c1" unitRef="tCO2e" decimals="2" name="esrs:Scope1GHGEmissions">{data.scope1.value}</ix:nonFraction></td>
            <td>{data.scope1.quality}%</td>
        </tr>
        <tr>
            <td>Scope 2 - Indirect Energy</td>
            <td><ix:nonFraction contextRef="c1" unitRef="tCO2e" decimals="2" name="esrs:Scope2GHGEmissions">{data.scope2.value}</ix:nonFraction></td>
            <td>{data.scope2.quality}%</td>
        </tr>
        <tr>
            <td>Scope 3 - Value Chain</td>
            <td><ix:nonFraction contextRef="c1" unitRef="tCO2e" decimals="2" name="esrs:Scope3GHGEmissions">{data.scope3.value}</ix:nonFraction></td>
            <td>{data.scope3.quality}%</td>
        </tr>
        <tr style="font-weight: bold;">
            <td>Total Emissions</td>
            <td><ix:nonFraction contextRef="c1" unitRef="tCO2e" decimals="2" name="esrs:TotalGHGEmissions">{data.scope1.value + data.scope2.value + data.scope3.value}</ix:nonFraction></td>
            <td>-</td>
        </tr>
    </table>
    
    <div style="margin-top: 40px; padding: 20px; background: #f9f9f9; border-radius: 8px;">
        <h3>Data Quality Information</h3>
        <p>Primary Data: {data.primary_data_percentage}%</p>
        <p>Estimates: {data.estimates_percentage}%</p>
        <p>Proxies: {data.proxies_percentage}%</p>
        <p>Verification Level: {data.verification_level}</p>
    </div>
    
    <div style="display:none">
        {xbrl_content}
    </div>
</body>
</html>"""
        return html