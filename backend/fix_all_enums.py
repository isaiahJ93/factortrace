#!/usr/bin/env python3
"""Add all missing ESRS enums"""

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# All the missing enums
all_enums = '''from enum import Enum

# GHG Protocol Scope 3 Categories
class Scope3Category(Enum):
    PURCHASED_GOODS_AND_SERVICES = "1. Purchased goods and services"
    CAPITAL_GOODS = "2. Capital goods"
    FUEL_AND_ENERGY_ACTIVITIES = "3. Fuel-and-energy-related activities"
    UPSTREAM_TRANSPORTATION = "4. Upstream transportation and distribution"
    WASTE_GENERATED = "5. Waste generated in operations"
    BUSINESS_TRAVEL = "6. Business travel"
    EMPLOYEE_COMMUTING = "7. Employee commuting"
    UPSTREAM_LEASED_ASSETS = "8. Upstream leased assets"
    DOWNSTREAM_TRANSPORTATION = "9. Downstream transportation and distribution"
    PROCESSING_OF_SOLD_PRODUCTS = "10. Processing of sold products"
    USE_OF_SOLD_PRODUCTS = "11. Use of sold products"
    END_OF_LIFE_TREATMENT = "12. End-of-life treatment of sold products"
    DOWNSTREAM_LEASED_ASSETS = "13. Downstream leased assets"
    FRANCHISES = "14. Franchises"
    INVESTMENTS = "15. Investments"

# ESRS Assurance Readiness Levels  
class AssuranceReadinessLevel(Enum):
    NOT_READY = "not_ready"
    PARTIALLY_READY = "partially_ready"
    MOSTLY_READY = "mostly_ready"
    FULLY_READY = "fully_ready"

'''

# Find where to insert (after SECTOR_SPECIFIC_REQUIREMENTS)
insert_pos = -1
for i, line in enumerate(lines):
    if 'SECTOR_SPECIFIC_REQUIREMENTS' in line:
        # Find the closing brace
        for j in range(i, len(lines)):
            if lines[j].strip() == '}':
                insert_pos = j + 2
                break
        break

if insert_pos == -1:
    insert_pos = 150

# Check if enums already exist
content = ''.join(lines)
if 'class Scope3Category' not in content:
    lines.insert(insert_pos, all_enums + '\n')
    print("✅ Added missing enums")
else:
    print("Enums already exist")

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)
