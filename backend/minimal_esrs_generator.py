#!/usr/bin/env python3
"""
Minimal ESRS E1 Generator - ONLY valid concepts
"""

def generate_minimal_esrs_e1_report(data):
    """Generate a minimal but VALID ESRS E1 report"""
    
    lei = data.get('lei', 'DEMO12345678901234AB')
    year = data.get('reporting_period', 2025)
    entity_name = data.get('entity_name', 'Test Company')
    
    # Get emission values with defaults
    scope1 = data.get('gross_scope1_emissions', 0)
    scope2 = data.get('gross_scope2_location_based', 0)
    scope3 = data.get('gross_scope3_emissions', 0)
    total = scope1 + scope2 + scope3
    
    # Create the MINIMAL valid XBRL report
    report = f'''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:link="http://www.xbrl.org/2003/linkbase"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:esrs="https://xbrl.efrag.org/taxonomy/esrs/2023-12-22"
      xmlns:iso4217="http://www.xbrl.org/2003/iso4217">
<head>
    <title>ESRS E1 Report - {entity_name}</title>
</head>
<body>
    <h1>ESRS E1 Climate Disclosures</h1>
    <h2>{entity_name} - {year}</h2>
    
    <section>
        <h3>GHG Emissions</h3>
        <p>Total GHG Emissions: 
            <ix:nonFraction name="esrs:GrossGreenhouseGasEmissions" 
                           contextRef="ctx-{year}" 
                           unitRef="tco2e" 
                           decimals="0">{total}</ix:nonFraction> tCO₂e
        </p>
        <p>Scope 1: 
            <ix:nonFraction name="esrs:GrossScope1GreenhouseGasEmissions" 
                           contextRef="ctx-{year}" 
                           unitRef="tco2e" 
                           decimals="0">{scope1}</ix:nonFraction> tCO₂e
        </p>
        <p>Scope 2 (Location-based): 
            <ix:nonFraction name="esrs:GrossLocationBasedScope2GreenhouseGasEmissions" 
                           contextRef="ctx-{year}" 
                           unitRef="tco2e" 
                           decimals="0">{scope2}</ix:nonFraction> tCO₂e
        </p>
        <p>Scope 3: 
            <ix:nonFraction name="esrs:GrossScope3GreenhouseGasEmissions" 
                           contextRef="ctx-{year}" 
                           unitRef="tco2e" 
                           decimals="0">{scope3}</ix:nonFraction> tCO₂e
        </p>
    </section>
    
    <div style="display:none">
        <ix:header>
            <ix:references>
                <link:schemaRef xlink:type="simple" 
                               xlink:href="https://xbrl.efrag.org/taxonomy/esrs/2023-12-22/common/esrs_cor.xsd"/>
            </ix:references>
            <ix:resources>
                <xbrli:context id="ctx-{year}">
                    <xbrli:entity>
                        <xbrli:identifier scheme="http://www.lei-worldwide.com">{lei}</xbrli:identifier>
                    </xbrli:entity>
                    <xbrli:period>
                        <xbrli:startDate>{year}-01-01</xbrli:startDate>
                        <xbrli:endDate>{year}-12-31</xbrli:endDate>
                    </xbrli:period>
                </xbrli:context>
                <xbrli:unit id="tco2e">
                    <xbrli:measure>esrs:tCO2e</xbrli:measure>
                </xbrli:unit>
            </ix:resources>
        </ix:header>
    </div>
</body>
</html>'''
    
    return {
        'content': report,
        'filename': f'esrs_e1_{year}.xhtml'
    }

if __name__ == '__main__':
    # Test the generator
    result = generate_minimal_esrs_e1_report({
        'entity_name': 'Test Corp',
        'reporting_period': 2025,
        'lei': 'TEST123456789012345',
        'gross_scope1_emissions': 1000,
        'gross_scope2_location_based': 500,
        'gross_scope3_emissions': 1500,
    })
    
    with open('minimal_esrs_output.xhtml', 'w') as f:
        f.write(result['content'])
    
    print("✅ Generated minimal_esrs_output.xhtml")
