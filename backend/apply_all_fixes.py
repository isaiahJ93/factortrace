import re

print("=== APPLYING ALL FIXES TO GENERATOR ===")

with open('./app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# 1. Fix namespaces
content = content.replace("'xmlns:esrs': 'http://xbrl.org/esrs/2023'", "'xmlns:esrs': 'https://xbrl.efrag.org/taxonomy/esrs/2023-12-22'")
content = content.replace("'xmlns:esrs': 'http://www.efrag.org/esrs/2023'", "'xmlns:esrs': 'https://xbrl.efrag.org/taxonomy/esrs/2023-12-22'")
print("✅ Fixed namespaces")

# 2. Fix schema
content = content.replace("'xlink:href': 'https://xbrl.efrag.org/taxonomy/esrs/2023-12-22/esrs_all.xsd'", "'xlink:href': 'https://xbrl.efrag.org/taxonomy/esrs/2023-12-22/common/esrs_cor.xsd'")
print("✅ Fixed schema reference")

# 3. Fix units
content = content.replace("'esrs:metricTonnesCO2e'", "'esrs:tCO2e'")
content = content.replace("'esrs:megawattHour'", "'esrs:MWh'")
print("✅ Fixed units")

# 4. Fix concept names
concepts = [
    ("'esrs-e1:TotalGHGEmissions'", "'esrs:GrossGreenhouseGasEmissions'"),
    ("'esrs-e1:GrossScope1Emissions'", "'esrs:GrossScope1GreenhouseGasEmissions'"),
    ("'esrs-e1:GrossScope2LocationBased'", "'esrs:GrossLocationBasedScope2GreenhouseGasEmissions'"),
    ("'esrs-e1:GrossScope3Emissions'", "'esrs:GrossScope3GreenhouseGasEmissions'"),
]
for old, new in concepts:
    content = content.replace(old, new)
print("✅ Fixed concept names")

# 5. Fix instant to duration periods
# This is more complex - need to find and replace instant period patterns
instant_pattern = r"(\s+)instant(\w*) = ET\.SubElement\((\w+), 'xbrli:instant'\)"
def replace_instant(match):
    indent = match.group(1)
    suffix = match.group(2)
    parent = match.group(3)
    return f"{indent}start_date{suffix} = ET.SubElement({parent}, 'xbrli:startDate')\n{indent}end_date{suffix} = ET.SubElement({parent}, 'xbrli:endDate')"

content = re.sub(instant_pattern, replace_instant, content)

# Fix instant.text patterns
content = re.sub(r"instant(\w*)\.text = f?['\"]?\{?(\w+)\}?-12-31['\"]?", r"start_date\1.text = f'{\2}-01-01'\n    end_date\1.text = f'{\2}-12-31'", content)
print("✅ Fixed periods")

# Save
with open('./app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("\n✅ All fixes applied successfully!")
