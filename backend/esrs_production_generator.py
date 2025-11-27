#!/usr/bin/env python3
"""
Production-ready ESRS E1 XBRL Generator
Produces valid ESRS reports with only emission facts
"""

def generate_production_esrs_e1(data):
    """Generate clean, valid ESRS E1 XBRL report"""
    
    # Extract data
    entity_name = data.get('entity_name', 'Company')
    lei = data.get('lei', 'DEMO12345678901234AB')
    year = data.get('reporting_period', 2025)
    
    # Emissions data
    scope1 = data.get('gross_scope1_emissions', 0)
    scope2 = data.get('gross_scope2_location_based', 0)
    scope3 = data.get('gross_scope3_emissions', 0)
    total = scope1 + scope2 + scope3
    
    # Generate clean XBRL
    xbrl_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:link="http://www.xbrl.org/2003/linkbase"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:esrs="https://xbrl.efrag.org/taxonomy/esrs/2023-12-22"
      xmlns:iso4217="http://www.xbrl.org/2003/iso4217">
<head>
    <title>ESRS E1 Report - {entity_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2 {{ color: #2c5530; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #2c5530; color: white; }}
        .total {{ font-weight: bold; background-color: #f0f0f0; }}
    </style>
</head>
<body>
    <h1>ESRS E1 Climate Disclosures</h1>
    <h2>{entity_name} - {year}</h2>
    
    <section>
        <h3>GHG Emissions (E1-6)</h3>
        <table>
            <thead>
                <tr>
                    <th>Emission Scope</th>
                    <th>Amount (tCO₂e)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Scope 1 (Direct emissions)</td>
                    <td><ix:nonFraction name="esrs:GrossScope1GreenhouseGasEmissions" 
                                       contextRef="period-{year}" 
                                       unitRef="tCO2e" 
                                       decimals="0">{scope1}</ix:nonFraction></td>
                </tr>
                <tr>
                    <td>Scope 2 (Location-based)</td>
                    <td><ix:nonFraction name="esrs:GrossLocationBasedScope2GreenhouseGasEmissions" 
                                       contextRef="period-{year}" 
                                       unitRef="tCO2e" 
                                       decimals="0">{scope2}</ix:nonFraction></td>
                </tr>
                <tr>
                    <td>Scope 3 (Value chain)</td>
                    <td><ix:nonFraction name="esrs:GrossScope3GreenhouseGasEmissions" 
                                       contextRef="period-{year}" 
                                       unitRef="tCO2e" 
                                       decimals="0">{scope3}</ix:nonFraction></td>
                </tr>
                <tr class="total">
                    <td>TOTAL GHG EMISSIONS</td>
                    <td><ix:nonFraction name="esrs:GrossGreenhouseGasEmissions" 
                                       contextRef="period-{year}" 
                                       unitRef="tCO2e" 
                                       decimals="0">{total}</ix:nonFraction></td>
                </tr>
            </tbody>
        </table>
    </section>
    
    <div style="display:none">
        <ix:header>
            <ix:references>
                <link:schemaRef xlink:type="simple" 
                               xlink:href="https://xbrl.efrag.org/taxonomy/esrs/2023-12-22/common/esrs_cor.xsd"/>
            </ix:references>
            <ix:resources>
                <xbrli:context id="period-{year}">
                    <xbrli:entity>
                        <xbrli:identifier scheme="http://www.lei-worldwide.com">{lei}</xbrli:identifier>
                    </xbrli:entity>
                    <xbrli:period>
                        <xbrli:startDate>{year}-01-01</xbrli:startDate>
                        <xbrli:endDate>{year}-12-31</xbrli:endDate>
                    </xbrli:period>
                </xbrli:context>
                <xbrli:unit id="tCO2e">
                    <xbrli:measure>esrs:tCO2e</xbrli:measure>
                </xbrli:unit>
            </ix:resources>
        </ix:header>
    </div>
</body>
</html>"""
    
    return {
        'content': xbrl_content,
        'filename': f'esrs_e1_{entity_name.lower().replace(" ", "_")}_{year}.xhtml'
    }

if __name__ == '__main__':
    # Test
    result = generate_production_esrs_e1({
        'entity_name': 'Example Corp',
        'reporting_period': 2025,
        'lei': 'EXMPL12345678901234',
        'gross_scope1_emissions': 1500,
        'gross_scope2_location_based': 750,
        'gross_scope3_emissions': 2250
    })
    print(f"Generated {result['filename']}")
