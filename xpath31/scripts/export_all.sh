#!/bin/bash
# Export to all formats

INPUT_FILE="$1"
BASE_NAME="${INPUT_FILE%.*}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Usage: ./export_all.sh input.xml"
    exit 1
fi

echo "=== Exporting to all formats ==="

# 1. Generate iXBRL/XHTML
echo "1. Creating iXBRL..."
./xpath31/scripts/ixbrl_formatter_clean.sh "$INPUT_FILE" "${BASE_NAME}.xhtml"

# 2. Generate JSON
echo "2. Creating JSON..."
./xpath31/scripts/export_json.sh "$INPUT_FILE" "${BASE_NAME}.json"

# 3. Generate PDF
echo "3. Creating PDF..."
./xpath31/scripts/export_pdf.sh "${BASE_NAME}.xhtml" "${BASE_NAME}.pdf"

echo ""
echo "✓ Export complete!"
echo "  - iXBRL: ${BASE_NAME}.xhtml"
echo "  - JSON:  ${BASE_NAME}.json"
echo "  - PDF:   ${BASE_NAME}.pdf"
