#!/bin/bash
# Test EFRAG/CSRD Taxonomy System

echo "=== Testing EFRAG/CSRD Taxonomy System ==="

# Test auto-tagging
echo -e "\n1. Testing auto-tagging..."
./xpath31/scripts/tagging/auto_tag.sh xpath31/tests/samples/test_sustainability_report.txt xpath31/tests/test_output.xml

# Show output
echo -e "\n2. Tagged output:"
cat xpath31/tests/test_output.xml

echo -e "\n=== Test complete ==="
