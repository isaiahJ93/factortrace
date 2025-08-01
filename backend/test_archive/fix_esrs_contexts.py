import re

filepath = '/Users/isaiah/Documents/Scope3Tool/backend/app/api/v1/endpoints/esrs_e1_full.py'

# Read the file
with open(filepath, 'r') as f:
    content = f.read()

# Find where contexts are added
pattern = r'(# Add contexts\s*\n.*?)(# Add units)'

# Create context additions
context_additions = '''
    # Add Scope 3 category contexts
    for i in range(1, 16):
        ctx = ET.SubElement(hidden_div, '{http://www.xbrl.org/2003/instance}context', 
                           {'id': f'c-cat{i}'})
        entity = ET.SubElement(ctx, '{http://www.xbrl.org/2003/instance}entity')
        identifier = ET.SubElement(entity, '{http://www.xbrl.org/2003/instance}identifier', 
                                  {'scheme': 'http://www.lei-worldwide.com'})
        identifier.text = lei
        period = ET.SubElement(ctx, '{http://www.xbrl.org/2003/instance}period')
        instant = ET.SubElement(period, '{http://www.xbrl.org/2003/instance}instant')
        instant.text = f"{reporting_period}-12-31"
    
    # Add intensity unit
    unit_intensity = ET.SubElement(hidden_div, '{http://www.xbrl.org/2003/instance}unit', 
                                  {'id': 'tCO2e-per-mEUR'})
    divide = ET.SubElement(unit_intensity, '{http://www.xbrl.org/2003/instance}divide')
    numerator = ET.SubElement(divide, '{http://www.xbrl.org/2003/instance}unitNumerator')
    num_measure = ET.SubElement(numerator, '{http://www.xbrl.org/2003/instance}measure')
    num_measure.text = 'esrs:metricTonnesCO2e'
    denominator = ET.SubElement(divide, '{http://www.xbrl.org/2003/instance}unitDenominator')
    den_measure = ET.SubElement(denominator, '{http://www.xbrl.org/2003/instance}measure')
    den_measure.text = 'iso4217:EUR'
    
'''

# Replace
new_content = re.sub(pattern, r'\1' + context_additions + r'\n    \2', content, flags=re.DOTALL)

with open(filepath, 'w') as f:
    f.write(new_content)

print("✅ Added missing contexts!")
