#!/bin/bash
# Complete EFRAG/CSRD Taxonomy Setup

echo "=== EFRAG/CSRD Taxonomy Setup ==="

# Create directory structure
echo "Creating directories..."
$(setup_taxonomy)

# Generate configuration files
echo "Generating taxonomy configuration..."
$(create_taxonomy_config)

# Create pattern files
echo "Creating pattern matching files..."
$(create_grep_patterns)

# Generate scripts
echo "Generating auto-tagging scripts..."
$(auto_tag_document)
$(create_validation_script)

# Create test data
echo "Creating test data..."
$(create_test_data)
$(create_test_suite)

# Create shortcuts
echo "Creating shortcuts..."
$(create_shortcuts)

# Create quick reference
cat > xpath31/QUICK_REFERENCE.md <<'DOC'
# EFRAG/CSRD Taxonomy Quick Reference

## Quick Start
1. Source shortcuts: `source xpath31/scripts/shortcuts.sh`
2. Tag a document: `qtag input.txt output.xml`
3. Validate output: `qval output.xml`
4. Run tests: `./xpath31/tests/run_tests.sh`

## Key Commands
- `qtag <input> [output]` - Quick tag a document
- `qval <xbrl_file>` - Validate XBRL file
- `fconcept <pattern>` - Find concept by pattern
- `lstandard <ESRS_X>` - List concepts for standard
- `xval <concept> [file]` - Extract values
- `csum` - Show concept summary
- `check_compliance <file>` - Check CSRD compliance

## Pattern Matching
```bash
# Find all emissions data
grep -E "scope.?[123].*emissions?" file.txt

# Find all percentages
grep -E "[0-9]+(\.[0-9]+)?%" file.txt

# Use pattern file
grep -E -f xpath31/taxonomy/patterns/efrag_patterns.txt file.txt
```

## Validation
```bash
# Schema validation
xmllint --schema xpath31/schemas/efrag-2023.xsd file.xml

# Check calculations
grep -A1 -B1 "TotalGHGEmissions" file.xml
```
DOC

echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. source xpath31/scripts/shortcuts.sh"
echo "2. ./xpath31/tests/run_tests.sh"
echo "3. qtag your_report.txt output.xml"
