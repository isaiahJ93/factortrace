# Fix the report that was just generated
with open('esrs_report_2025-08-01 (1).xhtml', 'r') as f:
    content = f.read()

# Apply ALL fixes
fixes = [
    # Namespace
    ('xmlns:esrs="http://xbrl.org/esrs/2023"', 'xmlns:esrs="https://xbrl.efrag.org/taxonomy/esrs/2023-12-22"'),
    # Schema
    ('esrs_all.xsd', 'common/esrs_cor.xsd'),
    # Units
    ('esrs:metricTonnesCO2e', 'esrs:tCO2e'),
    ('esrs:megawattHour', 'esrs:MWh'),
    # Concepts
    ('esrs-e1:TotalGHGEmissions', 'esrs:GrossGreenhouseGasEmissions'),
    ('esrs-e1:GrossScope1Emissions', 'esrs:GrossScope1GreenhouseGasEmissions'),
    ('esrs-e1:GrossScope2LocationBased', 'esrs:GrossLocationBasedScope2GreenhouseGasEmissions'),
    ('esrs-e1:GrossScope3Emissions', 'esrs:GrossScope3GreenhouseGasEmissions'),
]

for old, new in fixes:
    content = content.replace(old, new)

# Fix periods
import re
content = re.sub(
    r'<xbrli:instant>(\d{4})-12-31</xbrli:instant>',
    r'<xbrli:startDate>\1-01-01</xbrli:startDate>\n<xbrli:endDate>\1-12-31</xbrli:endDate>',
    content
)

# Remove non-ESRS concepts
non_esrs = ['EmissionsChangePercent', 'DataQualityScore', 'BoardOversightClimate', 
            'Scope3Category1', 'Scope3Category2', 'Scope3Category3']
for concept in non_esrs:
    pattern = f'<ix:[^>]*name="[^"]*:{concept}"[^>]*>[^<]*</ix:[^>]+>'
    content = re.sub(pattern, '<!-- REMOVED: Non-ESRS concept -->', content)

# Save fixed version
with open('esrs_report_FIXED.xhtml', 'w') as f:
    f.write(content)

print("✅ Created esrs_report_FIXED.xhtml")
