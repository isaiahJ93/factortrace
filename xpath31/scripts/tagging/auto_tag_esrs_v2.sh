#!/bin/bash
# Auto-tag ESRS Climate Disclosure Report - Fixed Version

INPUT_FILE="$1"
OUTPUT_FILE="${2:-tagged_output.xml}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    exit 1
fi

# Initialize output
echo '<?xml version="1.0" encoding="UTF-8"?>' > "$OUTPUT_FILE"
echo '<xbrl xmlns:esrs="https://xbrl.efrag.org/taxonomy/2023-12-31/esrs">' >> "$OUTPUT_FILE"
echo "  <context id='c1'>" >> "$OUTPUT_FILE"
echo "    <entity><identifier scheme='http://www.example.com'>COMPANY</identifier></entity>" >> "$OUTPUT_FILE"
echo "    <period><instant>2024-12-31</instant></period>" >> "$OUTPUT_FILE"
echo "  </context>" >> "$OUTPUT_FILE"

echo "Processing: $INPUT_FILE"

# Process Scope 1 emissions
if grep -q "GHG Emissions Scope 1:" "$INPUT_FILE"; then
    line=$(grep "GHG Emissions Scope 1:" "$INPUT_FILE")
    # Extract the number after the colon, handling commas
    value=$(echo "$line" | sed 's/.*: *//' | grep -oE '[0-9,]+' | head -1)
    if [ -n "$value" ]; then
        echo "  <esrs:GrossScope1Emissions contextRef='c1' unitRef='tCO2e'>$value</esrs:GrossScope1Emissions>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Scope 1 Emissions = $value tCO2e"
    fi
fi

# Process Scope 2 emissions
if grep -q "GHG Emissions Scope 2:" "$INPUT_FILE"; then
    line=$(grep "GHG Emissions Scope 2:" "$INPUT_FILE")
    value=$(echo "$line" | sed 's/.*: *//' | grep -oE '[0-9,]+' | head -1)
    if [ -n "$value" ]; then
        echo "  <esrs:GrossScope2MarketBased contextRef='c1' unitRef='tCO2e'>$value</esrs:GrossScope2MarketBased>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Scope 2 Emissions = $value tCO2e"
    fi
fi

# Process Scope 3 emissions
if grep -q "GHG Emissions Scope 3 - Total:" "$INPUT_FILE"; then
    line=$(grep "GHG Emissions Scope 3 - Total:" "$INPUT_FILE")
    value=$(echo "$line" | sed 's/.*: *//' | grep -oE '[0-9,]+' | head -1)
    if [ -n "$value" ]; then
        echo "  <esrs:GrossScope3Emissions contextRef='c1' unitRef='tCO2e'>$value</esrs:GrossScope3Emissions>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Scope 3 Emissions = $value tCO2e"
    fi
fi

# Calculate total emissions
scope1=$(grep "GHG Emissions Scope 1:" "$INPUT_FILE" | sed 's/.*: *//' | grep -oE '[0-9,]+' | head -1 | tr -d ',')
scope2=$(grep "GHG Emissions Scope 2:" "$INPUT_FILE" | sed 's/.*: *//' | grep -oE '[0-9,]+' | head -1 | tr -d ',')
scope3=$(grep "GHG Emissions Scope 3 - Total:" "$INPUT_FILE" | sed 's/.*: *//' | grep -oE '[0-9,]+' | head -1 | tr -d ',')

if [ -n "$scope1" ] && [ -n "$scope2" ] && [ -n "$scope3" ]; then
    total=$((scope1 + scope2 + scope3))
    # Format with comma
    total_formatted=$(printf "%'d" $total)
    echo "  <esrs:TotalGHGEmissions contextRef='c1' unitRef='tCO2e'>$total_formatted</esrs:TotalGHGEmissions>" >> "$OUTPUT_FILE"
    echo "✓ Tagged: Total GHG Emissions = $total_formatted tCO2e (calculated)"
fi

# Process Scope 3 categories
if grep -q "Purchased goods and services:" "$INPUT_FILE"; then
    line=$(grep "Purchased goods and services:" "$INPUT_FILE")
    value=$(echo "$line" | sed 's/.*: *//' | grep -oE '[0-9,]+' | head -1)
    if [ -n "$value" ]; then
        echo "  <esrs:Scope3Category1PurchasedGoods contextRef='c1' unitRef='tCO2e'>$value</esrs:Scope3Category1PurchasedGoods>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Scope 3 Cat 1 - Purchased goods = $value tCO2e"
    fi
fi

if grep -q "Capital goods:" "$INPUT_FILE"; then
    line=$(grep "Capital goods:" "$INPUT_FILE")
    value=$(echo "$line" | sed 's/.*: *//' | grep -oE '[0-9,]+' | head -1)
    if [ -n "$value" ]; then
        echo "  <esrs:Scope3Category2CapitalGoods contextRef='c1' unitRef='tCO2e'>$value</esrs:Scope3Category2CapitalGoods>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Scope 3 Cat 2 - Capital goods = $value tCO2e"
    fi
fi

# Process financial data
if grep -q "Revenue:" "$INPUT_FILE"; then
    line=$(grep "Revenue:" "$INPUT_FILE")
    value=$(echo "$line" | sed 's/.*EUR *//' | grep -oE '[0-9]+(\.[0-9]+)?' | head -1)
    if [ -n "$value" ]; then
        echo "  <esrs:Revenue contextRef='c1' unitRef='EUR' decimals='6'>$value</esrs:Revenue>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Revenue = EUR $value million"
    fi
fi

if grep -q "Total assets:" "$INPUT_FILE"; then
    line=$(grep "Total assets:" "$INPUT_FILE")
    value=$(echo "$line" | sed 's/.*EUR *//' | grep -oE '[0-9]+(\.[0-9]+)?' | head -1)
    if [ -n "$value" ]; then
        echo "  <esrs:TotalAssets contextRef='c1' unitRef='EUR' decimals='9'>$value</esrs:TotalAssets>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Total assets = EUR $value billion"
    fi
fi

if grep -q "Net profit:" "$INPUT_FILE"; then
    line=$(grep "Net profit:" "$INPUT_FILE")
    value=$(echo "$line" | sed 's/.*EUR *//' | grep -oE '[0-9]+(\.[0-9]+)?' | head -1)
    if [ -n "$value" ]; then
        echo "  <esrs:NetProfit contextRef='c1' unitRef='EUR' decimals='6'>$value</esrs:NetProfit>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Net profit = EUR $value million"
    fi
fi

# Add units definition
echo "  <unit id='tCO2e'><measure>esrs:tonnesCO2e</measure></unit>" >> "$OUTPUT_FILE"
echo "  <unit id='EUR'><measure>iso4217:EUR</measure></unit>" >> "$OUTPUT_FILE"

# Close XBRL document
echo "</xbrl>" >> "$OUTPUT_FILE"

echo "✓ Auto-tagging complete: $OUTPUT_FILE"
