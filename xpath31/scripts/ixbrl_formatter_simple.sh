#!/bin/bash
# Simple iXBRL Formatter that works with standard XML

INPUT_FILE="$1"
OUTPUT_FILE="${2:-output.xhtml}"

echo "Creating iXBRL document from: $INPUT_FILE"

# Create the iXBRL document using sed and awk for simplicity
cat > "$OUTPUT_FILE" << 'HEADER'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:esrs="https://xbrl.efrag.org/taxonomy/2023-12-31/esrs">
<head>
    <meta charset="UTF-8"/>
    <title>ESRS Sustainability Report - iXBRL Format</title>
    <style type="text/css">
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1, h2, h3 { color: #1f2937; }
        .metric { background-color: #e6f3ff; padding: 2px 6px; border-radius: 3px; font-weight: bold; }
        .context { display: none; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #e5e7eb; padding: 10px; text-align: left; }
        th { background-color: #f3f4f6; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9fafb; }
        .section { margin: 30px 0; }
        .highlight { color: #059669; font-weight: bold; }
    </style>
</head>
<body>
    <h1>ESRS Sustainability Report 2024</h1>
    <p>This report presents our sustainability performance in accordance with European Sustainability Reporting Standards (ESRS).</p>
    
    <div class="section">
        <h2>1. Climate Change (ESRS E1)</h2>
        <h3>1.1 GHG Emissions Performance</h3>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>2024 Performance</th>
                    <th>Unit</th>
                </tr>
            </thead>
            <tbody>
HEADER

# Extract values from XML and build the table
# Using grep and sed for simplicity
if grep -q "GrossScope1GHGEmissions" "$INPUT_FILE"; then
    value=$(grep "GrossScope1GHGEmissions" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << ROW
                <tr>
                    <td>Scope 1 Emissions</td>
                    <td class="metric">
                        <ix:nonFraction name="esrs:GrossScope1GHGEmissions" 
                                       contextRef="c2024" 
                                       unitRef="tCO2e" 
                                       decimals="0">${value}</ix:nonFraction>
                    </td>
                    <td>tCO2e</td>
                </tr>
ROW
fi

if grep -q "GrossScope2MarketBased" "$INPUT_FILE"; then
    value=$(grep "GrossScope2MarketBased" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << ROW
                <tr>
                    <td>Scope 2 Emissions (Market-based)</td>
                    <td class="metric">
                        <ix:nonFraction name="esrs:GrossScope2MarketBased" 
                                       contextRef="c2024" 
                                       unitRef="tCO2e" 
                                       decimals="0">${value}</ix:nonFraction>
                    </td>
                    <td>tCO2e</td>
                </tr>
ROW
fi

if grep -q "GrossScope3TotalEmissions" "$INPUT_FILE"; then
    value=$(grep "GrossScope3TotalEmissions" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << ROW
                <tr>
                    <td>Scope 3 Emissions</td>
                    <td class="metric">
                        <ix:nonFraction name="esrs:GrossScope3TotalEmissions" 
                                       contextRef="c2024" 
                                       unitRef="tCO2e" 
                                       decimals="0">${value}</ix:nonFraction>
                    </td>
                    <td>tCO2e</td>
                </tr>
ROW
fi

if grep -q "TotalGHGEmissions" "$INPUT_FILE"; then
    value=$(grep "TotalGHGEmissions" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << ROW
                <tr style="font-weight: bold; background-color: #f3f4f6;">
                    <td>Total GHG Emissions</td>
                    <td class="metric highlight">
                        <ix:nonFraction name="esrs:TotalGHGEmissions" 
                                       contextRef="c2024" 
                                       unitRef="tCO2e" 
                                       decimals="0">${value}</ix:nonFraction>
                    </td>
                    <td>tCO2e</td>
                </tr>
ROW
fi

cat >> "$OUTPUT_FILE" << 'SECTION2'
            </tbody>
        </table>
        
        <h3>1.2 Energy & Renewable Sources</h3>
SECTION2

if grep -q "RenewableEnergyPercentage" "$INPUT_FILE"; then
    value=$(grep "RenewableEnergyPercentage" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << ENERGY
        <p>Our renewable energy percentage reached 
            <span class="metric">
                <ix:nonFraction name="esrs:RenewableEnergyPercentage" 
                               contextRef="c2024" 
                               unitRef="pure" 
                               decimals="0">${value}</ix:nonFraction>%
            </span> in 2024.
        </p>
ENERGY
fi

if grep -q "TotalEnergyConsumption" "$INPUT_FILE"; then
    value=$(grep "TotalEnergyConsumption" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << ENERGY
        <p>Total energy consumption: 
            <span class="metric">
                <ix:nonFraction name="esrs:TotalEnergyConsumption" 
                               contextRef="c2024" 
                               unitRef="MWh" 
                               decimals="0">${value}</ix:nonFraction> MWh
            </span>
        </p>
ENERGY
fi

# Add Scope 3 breakdown if available
if grep -q "Scope3Category" "$INPUT_FILE"; then
    cat >> "$OUTPUT_FILE" << 'SCOPE3'
        
        <h3>1.3 Scope 3 Emissions Breakdown</h3>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Emissions</th>
                    <th>Unit</th>
                </tr>
            </thead>
            <tbody>
SCOPE3

    if grep -q "Scope3Category1PurchasedGoods" "$INPUT_FILE"; then
        value=$(grep "Scope3Category1PurchasedGoods" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
        cat >> "$OUTPUT_FILE" << CAT1
                <tr>
                    <td>Category 1: Purchased Goods and Services</td>
                    <td class="metric">
                        <ix:nonFraction name="esrs:Scope3Category1PurchasedGoods" 
                                       contextRef="c2024" 
                                       unitRef="tCO2e" 
                                       decimals="0">${value}</ix:nonFraction>
                    </td>
                    <td>tCO2e</td>
                </tr>
CAT1
    fi

    if grep -q "Scope3Category2CapitalGoods" "$INPUT_FILE"; then
        value=$(grep "Scope3Category2CapitalGoods" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
        cat >> "$OUTPUT_FILE" << CAT2
                <tr>
                    <td>Category 2: Capital Goods</td>
                    <td class="metric">
                        <ix:nonFraction name="esrs:Scope3Category2CapitalGoods" 
                                       contextRef="c2024" 
                                       unitRef="tCO2e" 
                                       decimals="0">${value}</ix:nonFraction>
                    </td>
                    <td>tCO2e</td>
                </tr>
CAT2
    fi

    echo "            </tbody></table>" >> "$OUTPUT_FILE"
fi

# Environmental Performance Section
cat >> "$OUTPUT_FILE" << 'ENV'
    </div>
    
    <div class="section">
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
ENV

# Water metrics
if grep -q "TotalWaterConsumption" "$INPUT_FILE"; then
    value=$(grep "TotalWaterConsumption" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << WATER
                <tr>
                    <td>Water Consumption</td>
                    <td class="metric">
                        <ix:nonFraction name="esrs:TotalWaterConsumption" 
                                       contextRef="c2024" 
                                       unitRef="m3" 
                                       decimals="0">${value}</ix:nonFraction>
                    </td>
                    <td>m³</td>
                </tr>
WATER
fi

# Waste metrics
if grep -q "WasteGenerated" "$INPUT_FILE"; then
    value=$(grep "WasteGenerated" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << WASTE
                <tr>
                    <td>Total Waste Generated</td>
                    <td class="metric">
                        <ix:nonFraction name="esrs:WasteGenerated" 
                                       contextRef="c2024" 
                                       unitRef="tonnes" 
                                       decimals="0">${value}</ix:nonFraction>
                    </td>
                    <td>tonnes</td>
                </tr>
WASTE
fi

if grep -q "WasteRecyclingRate" "$INPUT_FILE"; then
    value=$(grep "WasteRecyclingRate" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << RECYCLE
                <tr>
                    <td>Recycling Rate</td>
                    <td class="metric">
                        <ix:nonFraction name="esrs:WasteRecyclingRate" 
                                       contextRef="c2024" 
                                       unitRef="pure" 
                                       decimals="0">${value}</ix:nonFraction>%
                    </td>
                    <td>%</td>
                </tr>
RECYCLE
fi

# Social Performance Section
cat >> "$OUTPUT_FILE" << 'SOCIAL'
            </tbody>
        </table>
    </div>
    
    <div class="section">
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
SOCIAL

if grep -q "TotalEmployees" "$INPUT_FILE"; then
    value=$(grep "TotalEmployees" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << EMP
                <tr>
                    <td>Total Employees</td>
                    <td class="metric">
                        <ix:nonFraction name="esrs:TotalEmployees" 
                                       contextRef="c2024" 
                                       unitRef="pure" 
                                       decimals="0">${value}</ix:nonFraction>
                    </td>
                    <td>employees</td>
                </tr>
EMP
fi

if grep -q "GenderDiversityAllEmployees" "$INPUT_FILE"; then
    value=$(grep "GenderDiversityAllEmployees" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << GENDER
                <tr>
                    <td>Gender Diversity (% Female)</td>
                    <td class="metric">
                        <ix:nonFraction name="esrs:GenderDiversityAllEmployees" 
                                       contextRef="c2024" 
                                       unitRef="pure" 
                                       decimals="0">${value}</ix:nonFraction>%
                    </td>
                    <td>%</td>
                </tr>
GENDER
fi

# Close the document
cat >> "$OUTPUT_FILE" << 'FOOTER'
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>4. Governance (ESRS G1)</h2>
FOOTER

if grep -q "ConfirmedIncidentsOfCorruption" "$INPUT_FILE"; then
    value=$(grep "ConfirmedIncidentsOfCorruption" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << GOV
        <p>Confirmed corruption incidents: 
            <span class="metric">
                <ix:nonFraction name="esrs:ConfirmedIncidentsOfCorruption" 
                               contextRef="c2024" 
                               unitRef="pure" 
                               decimals="0">${value}</ix:nonFraction>
            </span>
        </p>
GOV
fi

cat >> "$OUTPUT_FILE" << 'END'
    </div>
    
    <!-- Hidden XBRL contexts -->
    <div style="display:none">
        <ix:header>
            <ix:hidden>
                <xbrli:context id="c2024">
                    <xbrli:entity>
                        <xbrli:identifier scheme="http://www.example.com">COMPANY-001</xbrli:identifier>
                    </xbrli:entity>
                    <xbrli:period>
                        <xbrli:instant>2024-12-31</xbrli:instant>
                    </xbrli:period>
                </xbrli:context>
                
                <xbrli:unit id="tCO2e"><xbrli:measure>esrs:tonnesCO2e</xbrli:measure></xbrli:unit>
                <xbrli:unit id="MWh"><xbrli:measure>esrs:MegawattHour</xbrli:measure></xbrli:unit>
                <xbrli:unit id="m3"><xbrli:measure>esrs:CubicMetre</xbrli:measure></xbrli:unit>
                <xbrli:unit id="tonnes"><xbrli:measure>esrs:Tonne</xbrli:measure></xbrli:unit>
                <xbrli:unit id="pure"><xbrli:measure>xbrli:pure</xbrli:measure></xbrli:unit>
            </ix:hidden>
        </ix:header>
    </div>
    
    <hr/>
    <p style="font-size: 0.9em; color: #6b7280; margin-top: 40px;">
        This document has been prepared in iXBRL format in accordance with the European Single Electronic Format (ESEF) 
        requirements and EFRAG's ESRS XBRL taxonomy.
    </p>
</body>
</html>
END

echo "✓ iXBRL document created: $OUTPUT_FILE"
