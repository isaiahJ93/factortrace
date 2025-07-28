#!/bin/bash
# EFRAG/CSRD Taxonomy Shortcuts

# Quick tag a file
qtag() {
    if [ -z "$1" ]; then
        echo "Usage: qtag <input_file> [output_file]"
        return 1
    fi
    ./xpath31/scripts/tagging/auto_tag.sh "$1" "${2:-quick_tagged.xml}"
}

# Quick validate
qval() {
    if [ -z "$1" ]; then
        echo "Usage: qval <xml_file>"
        return 1
    fi
    ./xpath31/scripts/validation/validate_taxonomy.sh "$1"
}

# Extract values by concept
xval() {
    local concept="$1"
    local file="${2:-*.xml}"
    grep "$concept" $file 2>/dev/null | sed 's/.*>\(.*\)<.*/\1/'
}

# List available patterns
lpat() {
    cat xpath31/taxonomy/patterns/efrag_patterns.txt | grep -v "^#" | grep -v "^$"
}

# Test the system
test_efrag() {
    echo "Testing EFRAG taxonomy system..."
    qtag xpath31/tests/samples/test_sustainability_report.txt xpath31/tests/test_output.xml
    echo -e "\nValidating output..."
    qval xpath31/tests/test_output.xml
}

echo "EFRAG/CSRD shortcuts loaded. Available commands:"
echo "  qtag <file>    - Auto-tag a document"
echo "  qval <file>    - Validate XBRL file"
echo "  xval <concept> - Extract concept values"
echo "  lpat           - List available patterns"
echo "  test_efrag     - Run a test"
