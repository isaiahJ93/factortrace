#!/bin/bash
# Test Complete ESRS Implementation

echo "=== Testing Complete ESRS Implementation ==="

# Create comprehensive test report
cat > xpath31/tests/comprehensive_report.txt << 'REPORT'
ESRS Comprehensive Sustainability Report 2024

ESRS 2 - General Disclosures
Board Composition: 12 members with 42% female representation
Independent directors: 75% of board members
Board meetings frequency: 12 times per year
Sustainability committee: Yes, established in 2020

Revenue: EUR 150 million
Total employees: 8,456
Total assets: EUR 2.5 billion
Net profit: EUR 25 million

ESRS E1 - Climate Change
Scope 1 emissions: 5,000 tCO2e
Scope 2 market-based emissions: 3,000 tCO2e
Scope 3 total emissions: 6,000 tCO2e
Total GHG emissions: 14,000 tCO2e

Renewable energy percentage: 67%
Total energy consumption: 125,000 MWh

Scope 3 Breakdown:
- Purchased goods and services: 4,000 tCO2e
- Capital goods: 2,000 tCO2e

ESRS E2 - Pollution
Air pollutants: 45 tonnes
NOx emissions: 12 tonnes
SOx emissions: 8 tonnes

ESRS E3 - Water
Total water consumption: 2,100,000 m3
Water withdrawal: 2,500,000 m3
Water intensity: 2.1 m3/unit

ESRS E4 - Biodiversity
Protected areas impacted: 0 hectares
Land use change: 5 hectares

ESRS E5 - Circular Economy
Total waste generated: 45,000 tonnes
Waste recycled: 37,800 tonnes
Recycling rate: 84%
Hazardous waste: 500 tonnes

ESRS S1 - Own Workforce
Total employees: 8,456
Female employees percentage: 45%
Gender pay gap: 12%
Average training hours: 32 hours
LTIFR: 0.23
Employee turnover rate: 8%

ESRS G1 - Business Conduct
Confirmed corruption incidents: 0
Political contributions: EUR 0
Lobbying expenditure: EUR 50,000
Whistleblowing cases: 3
REPORT

echo "1. Testing complete ESRS auto-tagging..."
./xpath31/scripts/tagging/auto_tag_complete_esrs.sh xpath31/tests/comprehensive_report.txt xpath31/tests/complete_esrs.xml

echo -e "\n2. Converting to iXBRL..."
./xpath31/scripts/ixbrl_formatter.sh xpath31/tests/complete_esrs.xml xpath31/tests/complete_esrs.xhtml

echo -e "\n3. Summary of tagged concepts:"
grep -o 'esrs:[^<]*' xpath31/tests/complete_esrs.xml | sort | uniq -c

echo -e "\n✓ Complete ESRS test finished"
echo "View iXBRL output: open xpath31/tests/complete_esrs.xhtml"
