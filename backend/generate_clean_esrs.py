import sys
sys.path.insert(0, '/Users/isaiah/Documents/Scope3Tool/backend')

# Import and monkey-patch to avoid minidom
import xml.etree.ElementTree as ET
from app.api.v1.endpoints.esrs_e1_full_clean import generate_xbrl_report

# Override format_xbrl_output to avoid minidom issues
def simple_format_output(html):
    # Convert to string
    xml_str = ET.tostring(html, encoding='unicode', method='xml')
    
    # Add XML declaration and DOCTYPE
    output = '<?xml version="1.0" encoding="UTF-8"?>\n'
    output += '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
    output += xml_str
    
    # Clean up empty names
    output = output.replace(' name=""', '')
    
    return output

# Monkey patch
import app.api.v1.endpoints.esrs_e1_full_clean
app.api.v1.endpoints.esrs_e1_full_clean.format_xbrl_output = simple_format_output

# Generate report
test_data = {
    'organization': 'Test Corp',
    'entity_name': 'Test Corp', 
    'lei': 'TEST123456789012345',
    'reporting_period': 2025,
    'emissions': {
        'scope1': 100,
        'scope2_location': 200,
        'scope3': 300
    }
}

report = generate_xbrl_report(test_data)

with open('production_output.xhtml', 'w') as f:
    f.write(report)

print(f"✅ Generated production_output.xhtml")
print(f"File size: {len(report):,} bytes")
print(f"Empty names: {report.count('name=\"\"')}")
print(f"Head tags: {report.count('<head>')}")
