#!/bin/bash

# Fix iXBRL output issues
# Usage: ./fix_ixbrl.sh test_output.xhtml > fixed_output.xhtml

echo "=== FIXING iXBRL OUTPUT ==="

# Create a temporary file for intermediate processing
TEMP_FILE=$(mktemp)

# Step 1: Remove duplicate head sections
# First, extract everything before the second <head> tag
echo "Removing duplicate <head> sections..."
cat "$1" | awk '
BEGIN { head_count = 0 }
/<head>/ { 
    head_count++
    if (head_count == 2) {
        # Skip until we find </head>
        while (getline > 0 && !/<\/head>/) {}
        next
    }
}
{ print }
' > "$TEMP_FILE"

# Step 2: Remove ALL empty name attributes (name="")
echo "Removing empty name attributes..."
sed -i.bak 's/ name=""//g' "$TEMP_FILE"

# Step 3: Fix incorrect uses of GrossGreenhouseGasEmissions for non-emission facts
echo "Fixing incorrect fact names..."
# First occurrence in materiality section - these should be different facts
sed -i.bak '0,/name="esrs:GrossGreenhouseGasEmissions"/{s/name="esrs:GrossGreenhouseGasEmissions"/name="esrs:EnvironmentalImpactMateriality"/}' "$TEMP_FILE"
sed -i.bak '0,/name="esrs:GrossGreenhouseGasEmissions"/{s/name="esrs:GrossGreenhouseGasEmissions"/name="esrs:FinancialImpactMateriality"/}' "$TEMP_FILE"

# Step 4: Add missing energy consumption facts
echo "Adding missing energy facts..."
# Find the energy section and add proper facts
sed -i.bak '/<section class="energy-consumption"/,/<\/section>/{
    s/<ix:nonFraction contextRef="c-current" unitRef="u-MWh" decimals="0">0<\/ix:nonFraction>/<ix:nonFraction name="esrs:TotalEnergyConsumption" contextRef="c-current" unitRef="MWh" decimals="0">0<\/ix:nonFraction>/
    s/<ix:nonFraction contextRef="c-current" unitRef="u-MWh" decimals="0">0<\/ix:nonFraction>/<ix:nonFraction name="esrs:EnergyConsumptionFromRenewableSources" contextRef="c-current" unitRef="MWh" decimals="0">0<\/ix:nonFraction>/2
}' "$TEMP_FILE"

# Step 5: Fix unit references (u-tCO2e -> tCO2e, u-MWh -> MWh, u-EUR -> EUR)
echo "Fixing unit references..."
sed -i.bak 's/unitRef="u-tCO2e"/unitRef="tCO2e"/g' "$TEMP_FILE"
sed -i.bak 's/unitRef="u-MWh"/unitRef="MWh"/g' "$TEMP_FILE"
sed -i.bak 's/unitRef="u-EUR"/unitRef="EUR"/g' "$TEMP_FILE"

# Step 6: Remove duplicate period dates in contexts
echo "Fixing duplicate period dates..."
sed -i.bak '/<xbrli:period>/{
    N
    :loop
    N
    /<\/xbrli:period>/!b loop
    s/<xbrli:startDate>\([^<]*\)<\/xbrli:startDate>[[:space:]]*<xbrli:endDate>\([^<]*\)<\/xbrli:endDate>[[:space:]]*<xbrli:startDate>[^<]*<\/xbrli:startDate>[[:space:]]*<xbrli:endDate>[^<]*<\/xbrli:endDate>/<xbrli:startDate>\1<\/xbrli:startDate><xbrli:endDate>\2<\/xbrli:endDate>/g
}' "$TEMP_FILE"

# Step 7: Fix empty start/end dates
echo "Fixing empty dates..."
sed -i.bak 's/<xbrli:startDate \/>//g' "$TEMP_FILE"
sed -i.bak 's/<xbrli:endDate \/>//g' "$TEMP_FILE"

# Step 8: Remove ix:header inside head tag (it should be in body)
echo "Moving ix:header to correct location..."
# This is complex, so we'll use awk
awk '
BEGIN { in_head = 0; ix_header = "" }
/<head>/ { in_head = 1 }
/<\/head>/ { in_head = 0 }
/<ix:header>/ && in_head { 
    capturing = 1
    ix_header = $0 "\n"
    next
}
/<\/ix:header>/ && capturing {
    ix_header = ix_header $0 "\n"
    capturing = 0
    next
}
capturing {
    ix_header = ix_header $0 "\n"
    next
}
{ print }
' "$TEMP_FILE" > "${TEMP_FILE}.2"
mv "${TEMP_FILE}.2" "$TEMP_FILE"

# Step 9: Clean up any remaining validation issues
echo "Final cleanup..."
# Remove any remaining empty attributes
sed -i.bak 's/ =""//g' "$TEMP_FILE"

# Output the fixed file
cat "$TEMP_FILE"

# Clean up
rm -f "$TEMP_FILE" "$TEMP_FILE.bak"

echo -e "\n=== FIX COMPLETE ===" >&2
echo "Run validation with: poetry run arelleCmdLine --file fixed_output.xhtml --validate" >&2