#!/bin/bash
# Validate XBRL against EFRAG taxonomy

INPUT_FILE="$1"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    exit 1
fi

echo "Validating: $INPUT_FILE"

# Check XML well-formedness
echo "Checking XML structure..."
if xmllint --noout "$INPUT_FILE" 2>/dev/null; then
    echo "✓ XML is well-formed"
else
    echo "❌ XML is not well-formed"
    xmllint "$INPUT_FILE" 2>&1 | head -5
fi

# Check for mandatory concepts
echo -e "\nChecking mandatory disclosures..."
mandatory_concepts=(
    "esrs:GrossScope1Emissions"
    "esrs:GrossScope2MarketBased"
    "esrs:TotalGHGEmissions"
)

for concept in "${mandatory_concepts[@]}"; do
    if grep -q "$concept" "$INPUT_FILE"; then
        value=$(grep "$concept" "$INPUT_FILE" | sed 's/.*>\(.*\)<.*/\1/')
        echo "✓ Found: $concept = $value"
    else
        echo "❌ Missing: $concept"
    fi
done

# Check calculations
echo -e "\nChecking calculations..."
if grep -q "esrs:GrossScope1Emissions" "$INPUT_FILE" && \
   grep -q "esrs:GrossScope2MarketBased" "$INPUT_FILE" && \
   grep -q "esrs:GrossScope3Emissions" "$INPUT_FILE" && \
   grep -q "esrs:TotalGHGEmissions" "$INPUT_FILE"; then
    
    scope1=$(grep "esrs:GrossScope1Emissions" "$INPUT_FILE" | sed 's/.*>\(.*\)<.*/\1/' | tr -d ',')
    scope2=$(grep "esrs:GrossScope2MarketBased" "$INPUT_FILE" | sed 's/.*>\(.*\)<.*/\1/' | tr -d ',')
    scope3=$(grep "esrs:GrossScope3Emissions" "$INPUT_FILE" | sed 's/.*>\(.*\)<.*/\1/' | tr -d ',')
    total=$(grep "esrs:TotalGHGEmissions" "$INPUT_FILE" | sed 's/.*>\(.*\)<.*/\1/' | tr -d ',')
    
    calculated=$(echo "$scope1 + $scope2 + $scope3" | bc)
    echo "Scope 1+2+3 = $scope1 + $scope2 + $scope3 = $calculated"
    echo "Total reported = $total"
    
    if [ "$calculated" = "$total" ]; then
        echo "✓ Calculation is correct"
    else
        echo "❌ Calculation mismatch"
    fi
fi

echo -e "\n✓ Validation complete"
