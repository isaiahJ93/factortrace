#!/bin/bash
# iXBRL (Inline XBRL) Formatter for ESRS Reporting

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
                
                <xbrli:context id="c2023">
                    <xbrli:entity>
                        <xbrli:identifier scheme="http://www.example.com/id">COMPANY-001</xbrli:identifier>
                    </xbrli:entity>
                    <xbrli:period>
                        <xbrli:instant>2023-12-31</xbrli:instant>
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

# Read the XBRL file
tree = ET.parse(input_file)
root = tree.getroot()

# Define namespace
ns = {'esrs': 'https://xbrl.efrag.org/taxonomy/2023-12-31/esrs'}

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
                <th>2023</th>
                <th>Change %</th>
            </tr>
        </thead>
        <tbody>
"""

# Extract values from XBRL
def get_value(concept):
    elem = root.find(f".//{concept}")
    return elem.text if elem is not None else "N/A"

# Add Scope 1 emissions
scope1 = get_value("esrs:GrossScope1GHGEmissions")
html_content += f"""
            <tr>
                <td>Scope 1 Emissions (tCO2e)</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:GrossScope1GHGEmissions" 
                                   contextRef="c2024" 
                                   unitRef="tCO2e" 
                                   decimals="0" 
                                   format="ixt:numdotcomma">{scope1}</ix:nonFraction>
                </td>
                <td>4,800</td>
                <td class="highlight">+4.2%</td>
            </tr>
"""

# Add Scope 2 emissions
scope2 = get_value("esrs:GrossScope2MarketBased")
html_content += f"""
            <tr>
                <td>Scope 2 Emissions - Market Based (tCO2e)</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:GrossScope2MarketBased" 
                                   contextRef="c2024" 
                                   unitRef="tCO2e" 
                                   decimals="0"
                                   format="ixt:numdotcomma">{scope2}</ix:nonFraction>
                </td>
                <td>3,200</td>
                <td class="highlight">-6.3%</td>
            </tr>
"""

# Add Scope 3 emissions
scope3 = get_value("esrs:GrossScope3TotalEmissions")
html_content += f"""
            <tr>
                <td>Scope 3 Emissions (tCO2e)</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:GrossScope3TotalEmissions" 
                                   contextRef="c2024" 
                                   unitRef="tCO2e" 
                                   decimals="0"
                                   format="ixt:numdotcomma">{scope3}</ix:nonFraction>
                </td>
                <td>5,800</td>
                <td class="highlight">+3.4%</td>
            </tr>
"""

# Add total emissions
total = get_value("esrs:TotalGHGEmissions")
html_content += f"""
            <tr style="font-weight: bold;">
                <td>Total GHG Emissions (tCO2e)</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:TotalGHGEmissions" 
                                   contextRef="c2024" 
                                   unitRef="tCO2e" 
                                   decimals="0"
                                   format="ixt:numdotcomma">{total}</ix:nonFraction>
                </td>
                <td>13,800</td>
                <td class="highlight">+1.4%</td>
            </tr>
        </tbody>
    </table>
"""

# Add Scope 3 breakdown if available
cat1 = get_value("esrs:Scope3Category1PurchasedGoods")
cat2 = get_value("esrs:Scope3Category2CapitalGoods")

if cat1 != "N/A" or cat2 != "N/A":
    html_content += """
    <h3>1.2 Scope 3 Emissions Breakdown</h3>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Emissions (tCO2e)</th>
                <th>% of Scope 3</th>
            </tr>
        </thead>
        <tbody>
"""
    
    if cat1 != "N/A":
        html_content += f"""
            <tr>
                <td>Category 1: Purchased Goods and Services</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:Scope3Category1PurchasedGoods" 
                                   contextRef="c2024" 
                                   unitRef="tCO2e" 
                                   decimals="0"
                                   format="ixt:numdotcomma">{cat1}</ix:nonFraction>
                </td>
                <td>66.7%</td>
            </tr>
"""
    
    if cat2 != "N/A":
        html_content += f"""
            <tr>
                <td>Category 2: Capital Goods</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:Scope3Category2CapitalGoods" 
                                   contextRef="c2024" 
                                   unitRef="tCO2e" 
                                   decimals="0"
                                   format="ixt:numdotcomma">{cat2}</ix:nonFraction>
                </td>
                <td>33.3%</td>
            </tr>
        </tbody>
    </table>
"""

# Add energy section
renewable = get_value("esrs:RenewableEnergyPercentage")
if renewable != "N/A":
    html_content += f"""
    <h3>1.3 Energy Management</h3>
    <p>Our renewable energy percentage reached 
        <ix:nonFraction name="esrs:RenewableEnergyPercentage" 
                       contextRef="c2024" 
                       unitRef="pure" 
                       decimals="1"
                       scale="-2"
                       format="ixt:num-dot-decimal">{renewable}</ix:nonFraction>
        in 2024, demonstrating our commitment to clean energy transition.
    </p>
"""

# Add financial metrics
revenue = get_value("esrs:Revenue")
assets = get_value("esrs:TotalAssets")
profit = get_value("esrs:NetProfit")

if any(v != "N/A" for v in [revenue, assets, profit]):
    html_content += """
    <h2>2. Financial Context</h2>
    <table>
        <thead>
            <tr>
                <th>Financial Metric</th>
                <th>2024</th>
                <th>Unit</th>
            </tr>
        </thead>
        <tbody>
"""
    
    if revenue != "N/A":
        html_content += f"""
            <tr>
                <td>Revenue</td>
                <td class="metric">
                    EUR <ix:nonFraction name="esrs:Revenue" 
                                       contextRef="c2024" 
                                       unitRef="EUR" 
                                       decimals="-6"
                                       format="ixt:num-dot-decimal">{revenue}</ix:nonFraction>
                </td>
                <td>million</td>
            </tr>
"""
    
    if assets != "N/A":
        html_content += f"""
            <tr>
                <td>Total Assets</td>
                <td class="metric">
                    EUR <ix:nonFraction name="esrs:TotalAssets" 
                                       contextRef="c2024" 
                                       unitRef="EUR" 
                                       decimals="-9"
                                       format="ixt:num-dot-decimal">{assets}</ix:nonFraction>
                </td>
                <td>billion</td>
            </tr>
"""
    
    if profit != "N/A":
        html_content += f"""
            <tr>
                <td>Net Profit</td>
                <td class="metric">
                    EUR <ix:nonFraction name="esrs:NetProfit" 
                                       contextRef="c2024" 
                                       unitRef="EUR" 
                                       decimals="-6"
                                       format="ixt:num-dot-decimal">{profit}</ix:nonFraction>
                </td>
                <td>million</td>
            </tr>
        </tbody>
    </table>
"""

# Close HTML
html_content += """
    <h2>3. Governance and Strategy</h2>
    <p>Our sustainability governance structure ensures robust oversight of climate-related risks and opportunities. 
    The Board of Directors reviews our climate strategy quarterly, with dedicated committees overseeing 
    implementation of our transition plan.</p>
    
    <h3>3.1 Transition Plan</h3>
    <p>We have developed a comprehensive transition plan aligned with the Paris Agreement's 1.5°C target. 
    Our science-based targets have been validated by the Science Based Targets initiative (SBTi).</p>
    
    <h2>4. Forward-Looking Statements</h2>
    <p>This report contains forward-looking statements regarding our sustainability targets and ambitions. 
    Actual results may differ materially from these statements due to various factors including regulatory 
    changes, market conditions, and technological developments.</p>
    
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
