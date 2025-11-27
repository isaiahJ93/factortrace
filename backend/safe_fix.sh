#!/bin/bash

# Safer iXBRL fix script that preserves the file structure
# Usage: ./safe_fix.sh test_output.xhtml

INPUT_FILE="$1"
OUTPUT_FILE="fixed_output.xhtml"

echo "=== SAFE iXBRL FIX ==="
echo "Input: $INPUT_FILE"
echo "Output: $OUTPUT_FILE"

# Step 1: Copy original file
cp "$INPUT_FILE" "$OUTPUT_FILE"

# Step 2: Remove duplicate head (keep first, remove second)
echo "1. Removing duplicate head..."
# This uses a more careful approach
perl -i -pe '
    if (/<head>/ && ++$head_count == 2) {
        $skip = 1;
    }
    if ($skip && /<\/head>/) {
        $skip = 0;
        $_ = "";
    }
    $_ = "" if $skip;
' "$OUTPUT_FILE"

# Step 3: Remove empty name attributes only
echo "2. Removing empty name attributes..."
sed -i.bak 's/ name=""//g' "$OUTPUT_FILE"

# Step 4: Fix unit references
echo "3. Fixing unit references..."
sed -i.bak 's/unitRef="u-tCO2e"/unitRef="tCO2e"/g' "$OUTPUT_FILE"
sed -i.bak 's/unitRef="u-MWh"/unitRef="MWh"/g' "$OUTPUT_FILE"
sed -i.bak 's/unitRef="u-EUR"/unitRef="EUR"/g' "$OUTPUT_FILE"

# Step 5: Verify the output
echo -e "\n=== VERIFICATION ==="
if [[ -s "$OUTPUT_FILE" ]]; then
    echo "✅ Output file exists and is not empty"
    echo "File size: $(wc -c < "$OUTPUT_FILE") bytes"
    echo "Head tags: $(grep -c '<head>' "$OUTPUT_FILE")"
    echo "Empty names: $(grep -c 'name=""' "$OUTPUT_FILE")"
    echo "Valid facts: $(grep -o 'name="esrs:[^"]*"' "$OUTPUT_FILE" | wc -l)"
    
    # Check if it's valid XML
    if xmllint --noout "$OUTPUT_FILE" 2>/dev/null; then
        echo "✅ Valid XML structure"
    else
        echo "❌ XML structure issues detected"
    fi
else
    echo "❌ ERROR: Output file is empty or missing!"
fi

# Clean up backup files
rm -f "${OUTPUT_FILE}.bak"

echo -e "\n=== DONE ==="
echo "Now run: poetry run arelleCmdLine --file $OUTPUT_FILE --validate"