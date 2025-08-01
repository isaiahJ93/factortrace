#!/bin/bash

echo "🔍 Deep iXBRL Implementation Diagnosis"
echo "====================================="

# 1. Check which endpoint is actually being used
echo -e "\n📍 Active Endpoint Check:"
echo "Which file is imported in api.py?"
grep -n "esrs" app/api/v1/api.py

# 2. Look at the actual implementation
echo -e "\n📄 Main Implementation Analysis:"
echo "Checking esrs_e1_full.py for iXBRL generation..."

# Check for the main function
grep -n "def generate_world_class_esrs_e1_ixbrl" app/api/v1/endpoints/esrs_e1_full.py

# Check for iXBRL element creation
echo -e "\n🏷️ iXBRL Element Creation:"
grep -A5 -B5 "nonFraction\|nonNumeric\|create_fact\|add_fact" app/api/v1/endpoints/esrs_e1_full.py | head -30

# 3. Check how facts are being created
echo -e "\n📊 Fact Creation Methods:"
grep -n "def.*fact\|def.*tag\|def.*element" app/api/v1/endpoints/esrs_e1_full.py | head -10

# 4. Look for the actual XHTML generation
echo -e "\n🌐 XHTML Generation:"
grep -A10 "DOCTYPE\|<html\|html.*Element" app/api/v1/endpoints/esrs_e1_full.py | head -20

# 5. Check response formatting
echo -e "\n📤 Response Format:"
grep -A10 "return.*xhtml\|xhtml_content\|Response\|JSONResponse" app/api/v1/endpoints/esrs_e1_full.py | head -20

# 6. Look for specific ESRS data handling
echo -e "\n📈 ESRS Data Processing:"
grep -n "scope1\|scope2\|scope3\|ghg_emissions" app/api/v1/endpoints/esrs_e1_full.py | head -10

# 7. Check the new implementation
echo -e "\n🆕 New Implementation Check (esrs_e1_full_new.py):"
grep -A5 "ix:nonFraction\|create.*fact" app/api/v1/endpoints/esrs_e1_full_new.py | head -20

# 8. Check for escape functions
echo -e "\n🔒 XML Escaping:"
grep -n "escape\|sanitize\|clean.*xml" app/api/v1/endpoints/esrs_e1_full.py

# 9. Check actual output structure
echo -e "\n📝 Sample Output Check:"
if [ -f "esrs_report_world_class.xhtml" ]; then
    echo "Checking latest generated file structure..."
    head -50 esrs_report_world_class.xhtml | grep -E "ix:|xbrli:|contextRef|unitRef|nonFraction|nonNumeric" | head -10
fi

echo -e "\n✅ Diagnosis Complete!"