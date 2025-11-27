#!/usr/bin/env python3
"""
Complete restructure of ghg_calculator.py dictionaries
"""

import re

# Read the original backup
backup_file = "app/api/v1/endpoints/ghg_calculator.py.backup_20250805_184516"
try:
    with open(backup_file, "r") as f:
        original_content = f.read()
    print(f"✓ Found backup file")
except:
    print("❌ No backup found, working with current file")
    with open("app/api/v1/endpoints/ghg_calculator.py", "r") as f:
        original_content = f.read()

# Extract everything before DEFAULT_EMISSION_FACTORS
before_def = original_content.split("DEFAULT_EMISSION_FACTORS")[0]

# Rebuild the file with properly formatted dictionaries
new_content = before_def + '''DEFAULT_EMISSION_FACTORS = {
    # Scope 1 - Direct Emissions
    "natural_gas_stationary": {
        "factor": 0.185,
        "unit": "kWh",
        "scope": "scope_1",
        "gas_composition": {"CO2": 0.99, "CH4": 0.01},
        "uncertainty": 2.0,
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "diesel_fleet": {
        "factor": 2.512,
        "unit": "litres",
        "scope": "scope_1",
        "gas_composition": {"CO2": 0.97, "CH4": 0.01, "N2O": 0.02},
        "uncertainty": 2.0,
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "petrol_fleet": {
        "factor": 2.194,
        "unit": "litres",
        "scope": "scope_1",
        "gas_composition": {"CO2": 0.97, "CH4": 0.01, "N2O": 0.02},
        "uncertainty": 2.0,
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "diesel_stationary": {
        "factor": 2.512,
        "unit": "litres",
        "scope": "scope_1",
        "gas_composition": {"CO2": 0.97, "CH4": 0.01, "N2O": 0.02},
        "uncertainty": 2.0,
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    # Scope 2 - Purchased Energy
    "electricity_grid": {
        "factor": 0.233,
        "unit": "kWh",
        "scope": "scope_2",
        "gas_composition": {"CO2": 1.0},
        "uncertainty": 5.0,
        "source": "DEFRA 2024 - UK Grid Electricity"
    },
    "electricity": {
        "factor": 0.233,
        "unit": "kWh",
        "scope": "scope_2",
        "gas_composition": {"CO2": 1.0},
        "uncertainty": 5.0,
        "source": "DEFRA 2024 - UK Grid Electricity"
    },
    "district_heating": {
        "factor": 0.210,
        "unit": "kWh",
        "scope": "scope_2",
        "gas_composition": {"CO2": 1.0},
        "uncertainty": 10.0,
        "source": "DEFRA 2024 - Heat and Steam"
    },
    # Scope 3 - Value Chain
    "waste_landfill": {
        "factor": 467.0,
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 5,
        "gas_composition": {"CO2": 0.3, "CH4": 0.7},
        "uncertainty": 40.0,
        "source": "DEFRA 2024 - Waste Disposal"
    },
    "office_paper": {
        "factor": 0.919,
        "unit": "kg",
        "scope": "scope_3",
        "category": 1,
        "gas_composition": {"CO2": 1.0},
        "uncertainty": 20.0,
        "source": "DEFRA 2024 - Material Use"
    },
    "plastic_packaging": {
        "factor": 3.131,
        "unit": "kg",
        "scope": "scope_3",
        "category": 1,
        "gas_composition": {"CO2": 1.0},
        "uncertainty": 25.0,
        "source": "DEFRA 2024 - Material Use"
    },
    "machinery": {
        "factor": 0.320,
        "unit": "USD",
        "scope": "scope_3",
        "category": 2,
        "gas_composition": {"CO2": 1.0},
        "uncertainty": 30.0,
        "source": "EPA EEIO 2024"
    },
    "buildings": {
        "factor": 380.000,
        "unit": "m²",
        "scope": "scope_3",
        "category": 2,
        "gas_composition": {"CO2": 1.0},
        "uncertainty": 30.0,
        "source": "RICS 2024"
    },
    "road_freight": {
        "factor": 0.105,
        "unit": "tonne.km",
        "scope": "scope_3",
        "category": 4,
        "gas_composition": {"CO2": 1.0},
        "uncertainty": 10.0,
        "source": "DEFRA 2024 - Freight Transport"
    },
    "business_travel_air": {
        "factor": 0.148,
        "unit": "passenger.km",
        "scope": "scope_3",
        "category": 6,
        "gas_composition": {"CO2": 1.0},
        "uncertainty": 10.0,
        "source": "DEFRA 2024 - Business Travel Air"
    },
    "employee_commuting": {
        "factor": 0.168,
        "unit": "km",
        "scope": "scope_3",
        "category": 7,
        "gas_composition": {"CO2": 1.0},
        "uncertainty": 20.0,
        "source": "DEFRA 2024 - Passenger Vehicles"
    }
}

# Category 3 WTT/T&D factors
CATEGORY_3_FACTORS = {
    "natural_gas": {
        "wtt_factor": 0.03255,
        "name": "Natural Gas WTT",
        "unit": "kWh",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "diesel": {
        "wtt_factor": 0.61314,
        "name": "Diesel WTT",
        "unit": "litres",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "petrol": {
        "wtt_factor": 0.59054,
        "name": "Petrol WTT",
        "unit": "litres",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "electricity": {
        "td_factor": 0.00979,
        "name": "Electricity T&D Losses",
        "unit": "kWh",
        "source": "DEFRA 2024 - UK Grid Electricity"
    },
    "district_heating": {
        "td_factor": 0.00883,
        "name": "District Heating T&D",
        "unit": "kWh",
        "source": "DEFRA 2024 - Heat and Steam"
    }
}

'''

# Now add the rest of the file after the dictionaries
# Find where the original code continues after emission factors
rest_of_file = re.search(r'(# ===== ESRS E1 MODELS =====.*)', original_content, re.DOTALL)
if rest_of_file:
    new_content += rest_of_file.group(1)
else:
    # Try another pattern
    rest_of_file = re.search(r'(class EnergyConsumption.*)', original_content, re.DOTALL)
    if rest_of_file:
        new_content += "\n" + rest_of_file.group(1)

# Write the fixed file
with open("app/api/v1/endpoints/ghg_calculator.py", "w") as f:
    f.write(new_content)

print("✅ Completely restructured ghg_calculator.py")

# Test import
try:
    from app.api.v1.endpoints.ghg_calculator import DEFAULT_EMISSION_FACTORS, CATEGORY_3_FACTORS
    print("✅ Successfully imported!")
    print(f"   - DEFAULT_EMISSION_FACTORS: {len(DEFAULT_EMISSION_FACTORS)} entries")
    print(f"   - CATEGORY_3_FACTORS: {len(CATEGORY_3_FACTORS)} entries")
except Exception as e:
    print(f"❌ Import still failing: {e}")
    import traceback
    traceback.print_exc()