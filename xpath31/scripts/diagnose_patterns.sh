#!/bin/bash
# Diagnostic script to find patterns in a document

INPUT_FILE="$1"

echo "=== Analyzing: $INPUT_FILE ==="
echo ""

echo "1. Looking for numbers with units:"
grep -oE '[0-9]{1,3}(,[0-9]{3})*(\.[0-9]+)?\s*(tCO2e?|tonnes?|%|MWh|m3|employees?)' "$INPUT_FILE"

echo -e "\n2. Looking for emission-related terms:"
grep -iE "(emission|carbon|CO2|GHG|greenhouse)" "$INPUT_FILE"

echo -e "\n3. Looking for scope mentions:"
grep -iE "scope\s*[123]" "$INPUT_FILE"

echo -e "\n4. Looking for energy-related terms:"
grep -iE "(energy|renewable|electricity|power)" "$INPUT_FILE"

echo -e "\n5. Looking for workforce-related terms:"
grep -iE "(employee|staff|workforce|headcount)" "$INPUT_FILE"

echo -e "\n6. All lines with numbers:"
grep -E '[0-9]+' "$INPUT_FILE"
