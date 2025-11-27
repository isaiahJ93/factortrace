import re

# Read the generator file
with open('./app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

print("=== FIXING ESRS GENERATOR ===")

# 1. Fix namespace URL
old_namespace = "'xmlns:esrs': 'http://xbrl.org/esrs/2023',"
new_namespace = "'xmlns:esrs': 'https://xbrl.efrag.org/taxonomy/esrs/2023-12-22',"
if old_namespace in content:
    content = content.replace(old_namespace, new_namespace)
    print("✅ Fixed namespace URL")

# 2. Fix schema reference
old_schema = "'xlink:href': 'https://xbrl.efrag.org/taxonomy/esrs/2023-12-22/esrs_all.xsd'"
new_schema = "'xlink:href': 'https://xbrl.efrag.org/taxonomy/esrs/2023-12-22/common/esrs_cor.xsd'"
if old_schema in content:
    content = content.replace(old_schema, new_schema)
    print("✅ Fixed schema reference")

# 3. Fix period type - find instant and replace with duration
# Look for patterns like: <xbrli:instant>{year}-12-31</xbrli:instant>
instant_pattern = r"<xbrli:instant>\{[^}]+\}-12-31</xbrli:instant>"
duration_replacement = "<xbrli:startDate>{year}-01-01</xbrli:startDate>\\n<xbrli:endDate>{year}-12-31</xbrli:endDate>"

# 4. Fix concept names
concept_fixes = [
    ("esrs-e1:GrossScope1Emissions", "esrs:GrossScope1GreenhouseGasEmissions"),
    ("esrs-e1:GrossScope2LocationBased", "esrs:GrossLocationBasedScope2GreenhouseGasEmissions"),
    ("esrs-e1:GrossScope3Emissions", "esrs:GrossScope3GreenhouseGasEmissions"),
    ("esrs-e1:TotalGHGEmissions", "esrs:GrossGreenhouseGasEmissions"),
    ("esrs-e1:GrossScope2MarketBased", "esrs:GrossMarketBasedScope2GreenhouseGasEmissions"),
]

for old, new in concept_fixes:
    if old in content:
        content = content.replace(old, new)
        print(f"✅ Fixed concept: {old} → {new}")

# 5. Fix unit measures
unit_fixes = [
    ("esrs:metricTonnesCO2e", "esrs:tCO2e"),
    ("esrs:megawattHour", "esrs:MWh"),
]

for old, new in unit_fixes:
    if old in content:
        content = content.replace(old, new)
        print(f"✅ Fixed unit: {old} → {new}")

# 6. Change <section> to <div>
if "<section " in content:
    content = content.replace("<section ", "<div ")
    content = content.replace("</section>", "</div>")
    print("✅ Changed section elements to div")

# Write the fixed file
with open('./app/api/v1/endpoints/esrs_e1_full_fixed.py', 'w') as f:
    f.write(content)

print("\n✅ Created fixed generator: esrs_e1_full_fixed.py")
print("Review the changes and then replace the original file")
