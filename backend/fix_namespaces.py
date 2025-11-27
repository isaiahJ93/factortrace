#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Register ALL namespaces BEFORE importing anything else
ET.register_namespace('', 'http://www.w3.org/1999/xhtml')
ET.register_namespace('ix', 'http://www.xbrl.org/2013/inlineXBRL')
ET.register_namespace('xbrli', 'http://www.xbrl.org/2003/instance')
ET.register_namespace('link', 'http://www.xbrl.org/2003/linkbase')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
ET.register_namespace('esrs', 'https://xbrl.efrag.org/taxonomy/esrs/2023-12-22')
ET.register_namespace('iso4217', 'http://www.xbrl.org/2003/iso4217')
ET.register_namespace('xbrldi', 'http://xbrl.org/2006/xbrldi')
ET.register_namespace('xbrldt', 'http://xbrl.org/2005/xbrldt')

# Now import
import sys
sys.path.insert(0, '/Users/isaiah/Documents/Scope3Tool/backend')
from app.api.v1.endpoints.esrs_e1_full import generate_xbrl_report as original_generate

def generate_clean_report(data):
    # Generate using original
    report = original_generate(data)
    
    # Clean up
    report = report.replace(' name=""', '')
    
    # Fix duplicate namespaces
    report = report.replace('xmlns:ns0=', 'xmlns:link=')
    report = report.replace('xmlns:ns1=', 'xmlns:xlink=')
    report = report.replace('xmlns:ns2=', 'xmlns:ix=')
    report = report.replace('xmlns:ns3=', 'xmlns:xbrli=')
    report = report.replace('<ns0:', '<link:')
    report = report.replace('</ns0:', '</link:')
    report = report.replace('<ns1:', '<xlink:')
    report = report.replace('</ns1:', '</xlink:')
    report = report.replace('<ns2:', '<ix:')
    report = report.replace('</ns2:', '</ix:')
    report = report.replace('<ns3:', '<xbrli:')
    report = report.replace('</ns3:', '</xbrli:')
    
    # Remove duplicate namespace declarations
    import re
    # Remove duplicate xmlns declarations
    for ns in ['xbrli', 'xlink', 'link', 'ix']:
        pattern = f'xmlns:{ns}="[^"]*"'
        matches = list(re.finditer(pattern, report))
        if len(matches) > 1:
            # Keep first, remove others
            for match in matches[1:]:
                report = report.replace(match.group(), '')
    
    return report

# Test
test_data = {
    'organization': 'Test Corp',
    'entity_name': 'Test Corp',
    'lei': 'TEST123456789012345',
    'reporting_period': 2025,
    'emissions': {'scope1': 100, 'scope2_location': 200, 'scope3': 300}
}

report = generate_clean_report(test_data)
with open('final_production.xhtml', 'w') as f:
    f.write(report)

print(f"✅ Generated final_production.xhtml")
print(f"File size: {len(report):,} bytes")
