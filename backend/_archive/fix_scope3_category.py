#!/usr/bin/env python3
"""Fix Scope3Category import issue"""

import os
import re

print("🔍 Finding where Scope3Category is defined...")

# Search for Scope3Category definition
scope3_location = None
for root, dirs, files in os.walk('app'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                if 'class Scope3Category' in content:
                    print(f"✅ Found Scope3Category in: {filepath}")
                    scope3_location = filepath
                    break
            except:
                pass
    if scope3_location:
        break

# Fix ghg_schemas.py
print("\n📋 Fixing ghg_schemas.py...")
with open('app/schemas/ghg_schemas.py', 'r') as f:
    content = f.read()

# Check if already has the import
if 'Scope3Category' not in content.split('\n')[0:30]:  # Check first 30 lines for import
    if scope3_location:
        # Add import from the found location
        module_path = scope3_location.replace('/', '.').replace('.py', '').replace('app.', '')
        import_line = f"from {module_path} import Scope3Category, CalculationMethod\n"
        
        # Add after other imports
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith(('from', 'import', '#', '"""')):
                lines.insert(i, import_line)
                break
        content = '\n'.join(lines)
    else:
        # Define it directly if not found
        print("⚠️  Scope3Category not found. Adding definition...")
        enum_def = '''
from enum import Enum

class Scope3Category(str, Enum):
    """GHG Protocol Scope 3 Categories"""
    PURCHASED_GOODS = "purchased_goods_and_services"
    CAPITAL_GOODS = "capital_goods"
    FUEL_AND_ENERGY = "fuel_and_energy_related"
    UPSTREAM_TRANSPORTATION = "upstream_transportation"
    WASTE_GENERATED = "waste_generated"
    BUSINESS_TRAVEL = "business_travel"
    EMPLOYEE_COMMUTING = "employee_commuting"
    UPSTREAM_LEASED = "upstream_leased_assets"
    DOWNSTREAM_TRANSPORTATION = "downstream_transportation"
    PROCESSING_SOLD_PRODUCTS = "processing_of_sold_products"
    USE_OF_SOLD_PRODUCTS = "use_of_sold_products"
    END_OF_LIFE = "end_of_life_treatment"
    DOWNSTREAM_LEASED = "downstream_leased_assets"
    FRANCHISES = "franchises"
    INVESTMENTS = "investments"

class CalculationMethod(str, Enum):
    """Calculation methodology types"""
    SPEND_BASED = "spend_based"
    ACTIVITY_BASED = "activity_based"
    HYBRID = "hybrid"
'''
        # Add after imports
        lines = content.split('\n')
        import_end = 0
        for i, line in enumerate(lines):
            if line.startswith(('from', 'import')):
                import_end = i
        
        lines.insert(import_end + 2, enum_def)
        content = '\n'.join(lines)

    # Write back
    with open('app/schemas/ghg_schemas.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed ghg_schemas.py")
else:
    print("✅ Scope3Category already imported/defined")

print("\n🚀 Now run: uvicorn app.main:app --reload --port 8000")