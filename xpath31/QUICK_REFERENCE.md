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
