#!/bin/bash
# Auto-tag document with EFRAG/CSRD concepts

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

# Function to extract numeric values
extract_value() {
    echo "$1" | grep -oE '[0-9]+([.,][0-9]+)?%?' | head -1
}

# Process Scope 1 emissions
if grep -qiE "scope.?1.{0,20}emissions?" "$INPUT_FILE"; then
    line=$(grep -iE "scope.?1.{0,20}emissions?" "$INPUT_FILE" | head -1)
    value=$(extract_value "$line")
    if [ -n "$value" ]; then
        echo "  <esrs:GrossScope1Emissions contextRef='c1'>$value</esrs:GrossScope1Emissions>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Scope 1 Emissions = $value"
    fi
fi

# Process Scope 2 emissions
if grep -qiE "scope.?2.{0,20}(market.?based|emissions)" "$INPUT_FILE"; then
    line=$(grep -iE "scope.?2.{0,20}(market.?based|emissions)" "$INPUT_FILE" | head -1)
    value=$(extract_value "$line")
    if [ -n "$value" ]; then
        echo "  <esrs:GrossScope2MarketBased contextRef='c1'>$value</esrs:GrossScope2MarketBased>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Scope 2 Emissions = $value"
    fi
fi

# Process Scope 3 emissions
if grep -qiE "scope.?3.{0,20}emissions?" "$INPUT_FILE"; then
    line=$(grep -iE "scope.?3.{0,20}emissions?" "$INPUT_FILE" | head -1)
    value=$(extract_value "$line")
    if [ -n "$value" ]; then
        echo "  <esrs:GrossScope3Emissions contextRef='c1'>$value</esrs:GrossScope3Emissions>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Scope 3 Emissions = $value"
    fi
fi

# Process Total GHG emissions
if grep -qiE "total.{0,20}(GHG|emissions)" "$INPUT_FILE"; then
    line=$(grep -iE "total.{0,20}(GHG|emissions)" "$INPUT_FILE" | head -1)
    value=$(extract_value "$line")
    if [ -n "$value" ]; then
        echo "  <esrs:TotalGHGEmissions contextRef='c1'>$value</esrs:TotalGHGEmissions>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Total GHG Emissions = $value"
    fi
fi

# Process renewable energy percentage
if grep -qiE "renewable.{0,20}energy.{0,20}(percentage|%)" "$INPUT_FILE"; then
    line=$(grep -iE "renewable.{0,20}energy.{0,20}(percentage|%)" "$INPUT_FILE" | head -1)
    value=$(extract_value "$line")
    if [ -n "$value" ]; then
        echo "  <esrs:RenewableEnergyPercentage contextRef='c1'>$value</esrs:RenewableEnergyPercentage>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Renewable Energy = $value"
    fi
fi

# Process total employees
if grep -qiE "(total.)?employees?|headcount" "$INPUT_FILE"; then
    line=$(grep -iE "(total.)?employees?|headcount" "$INPUT_FILE" | head -1)
    value=$(extract_value "$line")
    if [ -n "$value" ]; then
        echo "  <esrs:TotalEmployees contextRef='c1'>$value</esrs:TotalEmployees>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Total Employees = $value"
    fi
fi

# Process gender diversity
if grep -qiE "(female|women).{0,20}(percentage|%)" "$INPUT_FILE"; then
    line=$(grep -iE "(female|women).{0,20}(percentage|%)" "$INPUT_FILE" | head -1)
    value=$(extract_value "$line")
    if [ -n "$value" ]; then
        echo "  <esrs:GenderDiversity contextRef='c1'>$value</esrs:GenderDiversity>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Gender Diversity = $value"
    fi
fi

# Process corruption incidents
if grep -qiE "corruption.{0,20}incidents?" "$INPUT_FILE"; then
    line=$(grep -iE "corruption.{0,20}incidents?" "$INPUT_FILE" | head -1)
    value=$(extract_value "$line")
    if [ -n "$value" ]; then
        echo "  <esrs:ConfirmedCorruptionIncidents contextRef='c1'>$value</esrs:ConfirmedCorruptionIncidents>" >> "$OUTPUT_FILE"
        echo "✓ Tagged: Corruption Incidents = $value"
    fi
fi

# Close XBRL document
echo "</xbrl>" >> "$OUTPUT_FILE"

echo "✓ Auto-tagging complete: $OUTPUT_FILE"
