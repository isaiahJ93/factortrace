#!/bin/bash
# Fixed iXBRL (Inline XBRL) Formatter for ESRS Reporting

INPUT_FILE="$1"
OUTPUT_FILE="${2:-output.xhtml}"

# Function to create iXBRL document
create_ixbrl() {
    local input="$1"
    local output="$2"
    
    # Start XHTML document with iXBRL namespaces
    cat > "$output" << 'HEADER'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
      xmlns:esrs="https://xbrl.efrag.org/taxonomy/2023-12-31/esrs">
<head>
    <meta charset="UTF-8"/>
    <title>ESRS Sustainability Report - iXBRL Format</title>
    <style type="text/css">
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1, h2, h3 { color: #1f2937; }
        .metric { background-color: #f0f9ff; padding: 2px 4px; border-radius: 3px; }
        .context { display: none; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #e5e7eb; padding: 8px; text-align: left; }
        th { background-color: #f3f4f6; font-weight: bold; }
        .highlight { background-color: #fef3c7; }
    </style>
</head>
<body>
    <!-- Hidden contexts for iXBRL -->
    <div class="context">
        <ix:header>
            <ix:hidden>
                <xbrli:context id="c2024">
                    <xbrli:entity>
                        <xbrli:identifier scheme="http://www.example.com/id">COMPANY-001</xbrli:identifier>
                    </xbrli:entity>
                    <xbrli:period>
                        <xbrli:instant>2024-12-31</xbrli:instant>
                    </xbrli:period>
                </xbrli:context>
                
                <xbrli:unit id="EUR">
                    <xbrli:measure>iso4217:EUR</xbrli:measure>
                </xbrli:unit>
                
                <xbrli:unit id="tCO2e">
                    <xbrli:measure>esrs:tonnesCO2e</xbrli:measure>
                </xbrli:unit>
                
                <xbrli:unit id="MWh">
                    <xbrli:measure>esrs:MegawattHour</xbrli:measure>
                </xbrli:unit>
                
                <xbrli:unit id="m3">
                    <xbrli:measure>esrs:CubicMetre</xbrli:measure>
                </xbrli:unit>
                
                <xbrli:unit id="tonnes">
                    <xbrli:measure>esrs:Tonne</xbrli:measure>
                </xbrli:unit>
                
                <xbrli:unit id="pure">
                    <xbrli:measure>xbrli:pure</xbrli:measure>
                </xbrli:unit>
            </ix:hidden>
        </ix:header>
    </div>
HEADER

    # Process the input file and convert to iXBRL
    python3 - "$input" "$output" << 'PYTHON'
import sys
import re
import xml.etree.ElementTree as ET

input_file = sys.argv[1]
output_file = sys.argv[2]

# Parse XBRL with namespace
ET.register_namespace('esrs', 'https://xbrl.efrag.org/taxonomy/2023-12-31/esrs')
ET.register_namespace('xbrli', 'http://www.xbrl.org/2003/instance')

tree = ET.parse(input_file)
root = tree.getroot()

# Create HTML content with inline XBRL tags
html_content = """
    <h1>ESRS Sustainability Report 2024</h1>
    <p>This report presents our sustainability performance in accordance with European Sustainability Reporting Standards (ESRS).</p>
    
    <h2>1. Climate Change (ESRS E1)</h2>
    
    <h3>1.1 GHG Emissions Performance</h3>
    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>2024</th>
                <th>Unit</th>
            </tr>
        </thead>
        <tbody>
"""

# Helper function to extract values
def get_value(concept_name):
    # Search without namespace prefix first
    elem = root.find(f".//{{{root.nsmap.get('esrs', 'https://xbrl.efrag.org/taxonomy/2023-12-31/esrs')}}}{concept_name}")
    if elem is None:
        # Try with different namespace combinations
        for elem in root.iter():
            if elem.tag.endswith(concept_name):
                return elem.text
    return elem.text if elem is not None else None

# Extract and format emissions data
emissions_data = [
    ("GrossScope1GHGEmissions", "Scope 1 Emissions", "tCO2e"),
    ("GrossScope2MarketBased", "Scope 2 Emissions (Market-based)", "tCO2e"),
    ("GrossScope3TotalEmissions", "Scope 3 Emissions", "tCO2e"),
    ("TotalGHGEmissions", "Total GHG Emissions", "tCO2e")
]

for concept, label, unit in emissions_data:
    value = get_value(concept)
    if value:
        html_content += f"""
            <tr>
                <td>{label}</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:{concept}" 
                                   contextRef="c2024" 
                                   unitRef="{unit}" 
                                   decimals="0" 
                                   format="ixt:numdotcomma">{value}</ix:nonFraction>
                </td>
                <td>{unit}</td>
            </tr>
"""

html_content += """
        </tbody>
    </table>
"""

# Add energy metrics
energy_value = get_value("RenewableEnergyPercentage")
if energy_value:
    html_content += f"""
    <h3>1.2 Energy Management</h3>
    <p>Renewable energy percentage: 
        <ix:nonFraction name="esrs:RenewableEnergyPercentage" 
                       contextRef="c2024" 
                       unitRef="pure" 
                       decimals="0"
                       format="ixt:num-dot-decimal">{energy_value}</ix:nonFraction>%
    </p>
"""

# Add other environmental metrics
html_content += """
    <h2>2. Environmental Performance</h2>
    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>2024 Performance</th>
                <th>Unit</th>
            </tr>
        </thead>
        <tbody>
"""

env_metrics = [
    ("TotalWaterConsumption", "Water Consumption", "m³", "m3"),
    ("WasteGenerated", "Waste Generated", "tonnes", "tonnes"),
    ("WasteRecyclingRate", "Recycling Rate", "%", "pure")
]

for concept, label, display_unit, xbrl_unit in env_metrics:
    value = get_value(concept)
    if value:
        if display_unit == "%":
            html_content += f"""
            <tr>
                <td>{label}</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:{concept}" 
                                   contextRef="c2024" 
                                   unitRef="{xbrl_unit}" 
                                   decimals="0">{value}</ix:nonFraction>%
                </td>
                <td>{display_unit}</td>
            </tr>
"""
        else:
            html_content += f"""
            <tr>
                <td>{label}</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:{concept}" 
                                   contextRef="c2024" 
                                   unitRef="{xbrl_unit}" 
                                   decimals="0"
                                   format="ixt:numdotcomma">{value}</ix:nonFraction>
                </td>
                <td>{display_unit}</td>
            </tr>
"""

html_content += """
        </tbody>
    </table>
"""

# Add social metrics
html_content += """
    <h2>3. Social Performance (ESRS S1)</h2>
    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>2024 Performance</th>
                <th>Unit</th>
            </tr>
        </thead>
        <tbody>
"""

social_metrics = [
    ("TotalEmployees", "Total Employees", "employees", "pure"),
    ("GenderDiversityAllEmployees", "Gender Diversity", "%", "pure"),
    ("GenderPayGap", "Gender Pay Gap", "%", "pure"),
    ("WorkRelatedInjuries", "LTIFR", "rate", "pure")
]

for concept, label, display_unit, xbrl_unit in social_metrics:
    value = get_value(concept)
    if value:
        if display_unit == "%":
            html_content += f"""
            <tr>
                <td>{label}</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:{concept}" 
                                   contextRef="c2024" 
                                   unitRef="{xbrl_unit}" 
                                   decimals="0">{value}</ix:nonFraction>%
                </td>
                <td>{display_unit}</td>
            </tr>
"""
        else:
            html_content += f"""
            <tr>
                <td>{label}</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:{concept}" 
                                   contextRef="c2024" 
                                   unitRef="{xbrl_unit}" 
                                   decimals="0"
                                   format="ixt:numdotcomma">{value}</ix:nonFraction>
                </td>
                <td>{display_unit}</td>
            </tr>
"""

html_content += """
        </tbody>
    </table>
"""

# Add governance metrics
html_content += """
    <h2>4. Governance (ESRS G1)</h2>
    <p>Confirmed corruption incidents: 
        <ix:nonFraction name="esrs:ConfirmedIncidentsOfCorruption" 
                       contextRef="c2024" 
                       unitRef="pure" 
                       decimals="0">"""

corruption = get_value("ConfirmedIncidentsOfCorruption")
if corruption:
    html_content += f"{corruption}</ix:nonFraction>"

html_content += """
    </p>
    
    <hr/>
    <p style="font-size: 0.9em; color: #6b7280;">
        This document has been prepared in iXBRL format in accordance with the European Single Electronic Format (ESEF) 
        requirements and EFRAG's ESRS XBRL taxonomy.
    </p>
"""

# Write to output file
with open(output_file, 'r') as f:
    content = f.read()

# Insert the HTML content before closing body tag
content = content.replace('</body>', html_content + '\n</body>')

with open(output_file, 'w') as f:
    f.write(content)

print(f"✓ iXBRL document created: {output_file}")
PYTHON

    # Close the HTML document
    echo "</body></html>" >> "$output"
}

# Main execution
echo "Creating iXBRL document from: $INPUT_FILE"
create_ixbrl "$INPUT_FILE" "$OUTPUT_FILE"
