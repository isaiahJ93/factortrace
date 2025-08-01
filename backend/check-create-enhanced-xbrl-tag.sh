#!/bin/bash

echo "🔍 Checking create_enhanced_xbrl_tag implementation..."
echo "=================================================="

# Find the function definition
echo -e "\n📄 Function Definition:"
grep -A30 "def create_enhanced_xbrl_tag" app/api/v1/endpoints/esrs_e1_full.py

# Check what namespace is being used
echo -e "\n🏷️ Namespace Usage:"
grep -B5 -A5 "http://www.xbrl.org/2013/inlineXBRL" app/api/v1/endpoints/esrs_e1_full.py | head -20

# Check how the function is called
echo -e "\n📞 Function Calls:"
grep -B2 -A2 "create_enhanced_xbrl_tag" app/api/v1/endpoints/esrs_e1_full.py | head -30

# Check the return format
echo -e "\n📤 Return Format:"
grep -A10 "return {" app/api/v1/endpoints/esrs_e1_full.py | grep -E "content|filename|xhtml" | head -10

# Check if there's a simpler working example
echo -e "\n🔍 Looking for working iXBRL examples:"
grep -l "ix:nonFraction\|ix:nonNumeric" *.py | head -5

echo -e "\n✅ Done!"