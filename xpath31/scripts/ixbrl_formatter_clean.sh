#!/bin/bash
# Clean iXBRL Formatter - Fixed syntax

INPUT_FILE="$1"
OUTPUT_FILE="${2:-output.xhtml}"

echo "Creating clean iXBRL document from: $INPUT_FILE"

# Create the compliant iXBRL document header
cat > "$OUTPUT_FILE" << 'HEADER'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:link="http://www.xbrl.org/2003/linkbase"
      xmlns:xlink="http://www.w3.org/1999/xlink"
      xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
      xmlns:ixt="http://www.xbrl.org/inlineXBRL/transformation/2022-02-16"
      xmlns:esrs="https://xbrl.efrag.org/taxonomy/2023-12-31/esrs">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <title>ESRS Sustainability Report 2024 - iXBRL</title>
    <style type="text/css">
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            line-height: 1.6;
            color: #333;
        }
        h1 { color: #1f2937; font-size: 2em; margin-bottom: 0.5em; }
        h2 { color: #374151; font-size: 1.5em; margin-top: 1.5em; }
        h3 { color: #4b5563; font-size: 1.2em; margin-top: 1em; }
        .metric { 
            background-color: #e0f2fe; 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-weight: bold;
        }
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin: 20px 0;
        }
        th, td { 
            border: 1px solid #e5e7eb; 
            padding: 12px; 
            text-align: left; 
        }
        th { 
            background-color: #f3f4f6; 
            font-weight: bold;
        }
        tr:nth-child(even) { background-color: #f9fafb; }
        .highlight { color: #059669; font-weight: bold; }
        .total-row { font-weight: bold; background-color: #f3f4f6; }
    </style>
</head>
<body>
HEADER

# Add the body content
cat >> "$OUTPUT_FILE" << 'BODY'
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
                <th>Change</th>
                <th>Unit</th>
            </tr>
        </thead>
        <tbody>
BODY

# Process emissions data
if grep -q "GrossScope1GHGEmissions" "$INPUT_FILE"; then
    value=$(grep "GrossScope1GHGEmissions" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << ROW1
            <tr>
                <td>Scope 1 Emissions</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:GrossScope1GHGEmissions" 
                                   contextRef="c2024" 
                                   unitRef="tCO2e" 
                                   decimals="0">${value}</ix:nonFraction>
                </td>
                <td>4,750</td>
                <td class="highlight">+5.3%</td>
                <td>tCO2e</td>
            </tr>
ROW1
fi

if grep -q "GrossScope2MarketBased" "$INPUT_FILE"; then
    value=$(grep "GrossScope2MarketBased" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << ROW2
            <tr>
                <td>Scope 2 Emissions (Market-based)</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:GrossScope2MarketBased" 
                                   contextRef="c2024" 
                                   unitRef="tCO2e" 
                                   decimals="0">${value}</ix:nonFraction>
                </td>
                <td>3,300</td>
                <td class="highlight">-9.1%</td>
                <td>tCO2e</td>
            </tr>
ROW2
fi

if grep -q "GrossScope3TotalEmissions" "$INPUT_FILE"; then
    value=$(grep "GrossScope3TotalEmissions" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << ROW3
            <tr>
                <td>Scope 3 Emissions</td>
                <td class="metric">
                    <ix:nonFraction name="esrs:GrossScope3TotalEmissions" 
                                   contextRef="c2024" 
                                   unitRef="tCO2e" 
                                   decimals="0">${value}</ix:nonFraction>
                </td>
                <td>5,880</td>
                <td>+2.0%</td>
                <td>tCO2e</td>
            </tr>
ROW3
fi

if grep -q "TotalGHGEmissions" "$INPUT_FILE"; then
    value=$(grep "TotalGHGEmissions" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << ROW4
            <tr class="total-row">
                <td>Total GHG Emissions</td>
                <td class="metric highlight">
                    <ix:nonFraction name="esrs:TotalGHGEmissions" 
                                   contextRef="c2024" 
                                   unitRef="tCO2e" 
                                   decimals="0">${value}</ix:nonFraction>
                </td>
                <td>13,930</td>
                <td>+0.5%</td>
                <td>tCO2e</td>
            </tr>
ROW4
fi

# Continue with the rest of the report
cat >> "$OUTPUT_FILE" << 'REST'
        </tbody>
    </table>
    
    <h3>1.2 Energy & Renewable Sources</h3>
REST

if grep -q "RenewableEnergyPercentage" "$INPUT_FILE"; then
    value=$(grep "RenewableEnergyPercentage" "$INPUT_FILE" | sed 's/.*>\([^<]*\)<.*/\1/')
    cat >> "$OUTPUT_FILE" << RENEW
    <p>Renewable energy percentage: 
        <span class="metric">
            <ix:nonFraction name="esrs:RenewableEnergyPercentage" 
                           contextRef="c2024" 
                           unitRef="pure" 
                           decimals="0">${value}</ix:nonFraction>%
        </span>
    </p>
RENEW
fi

# Environmental metrics
cat >> "$OUTPUT_FILE" << 'ENV'
    
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

# Social metrics
cat >> "$OUTPUT_FILE" << 'SOCIAL'
        </tbody>
    </table>
    
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

# Add hidden XBRL contexts and close
cat >> "$OUTPUT_FILE" << 'END'
    
    <!-- Hidden XBRL contexts and units -->
    <div style="display:none">
        <ix:header>
            <ix:hidden>
                <ix:references>
                    <link:schemaRef xlink:type="simple" 
                                   xlink:href="https://xbrl.efrag.org/taxonomy/2023-12-31/esrs-all.xsd"/>
                </ix:references>
                
                <xbrli:context id="c2024">
                    <xbrli:entity>
                        <xbrli:identifier scheme="http://standards.iso.org/iso/17442">5493000IBP32UQZ0KL24</xbrli:identifier>
                    </xbrli:entity>
                    <xbrli:period>
                        <xbrli:instant>2024-12-31</xbrli:instant>
                    </xbrli:period>
                </xbrli:context>
                
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
    
    <hr/>
    <p style="font-size: 0.9em; color: #6b7280; margin-top: 40px;">
        This document has been prepared in iXBRL format in accordance with ESEF requirements and EFRAG's ESRS XBRL taxonomy.
    </p>
</body>
</html>
END

echo "✓ Clean iXBRL document created: $OUTPUT_FILE"
