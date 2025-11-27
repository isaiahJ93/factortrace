#!/usr/bin/env python3
"""
Fix activity type mappings and Category 3 calculation logic
"""

# Read the file
with open("app/api/v1/endpoints/ghg_calculator.py", "r") as f:
    content = f.read()

# Add aliases to DEFAULT_EMISSION_FACTORS
# Find the position after diesel_fleet definition
diesel_fleet_end = content.find('"diesel_fleet": {')
if diesel_fleet_end > 0:
    # Find the closing brace for diesel_fleet
    brace_count = 0
    pos = content.find('{', diesel_fleet_end)
    while pos < len(content):
        if content[pos] == '{':
            brace_count += 1
        elif content[pos] == '}':
            brace_count -= 1
            if brace_count == 0:
                # Found the end, insert diesel alias
                insert_pos = content.find('\n', pos) + 1
                diesel_alias = '''    "diesel": {
        "factor": 2.512,
        "unit": "litres",
        "scope": "scope_1",
        "gas_composition": {"CO2": 0.97, "CH4": 0.01, "N2O": 0.02},
        "uncertainty": 2.0,
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
'''
                content = content[:insert_pos] + diesel_alias + content[insert_pos:]
                break
        pos += 1

# Do the same for petrol
petrol_fleet_end = content.find('"petrol_fleet": {')
if petrol_fleet_end > 0:
    brace_count = 0
    pos = content.find('{', petrol_fleet_end)
    while pos < len(content):
        if content[pos] == '{':
            brace_count += 1
        elif content[pos] == '}':
            brace_count -= 1
            if brace_count == 0:
                insert_pos = content.find('\n', pos) + 1
                petrol_alias = '''    "petrol": {
        "factor": 2.194,
        "unit": "litres",
        "scope": "scope_1",
        "gas_composition": {"CO2": 0.97, "CH4": 0.01, "N2O": 0.02},
        "uncertainty": 2.0,
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
'''
                content = content[:insert_pos] + petrol_alias + content[insert_pos:]
                break
        pos += 1

# Fix the Category 3 calculation logic to handle missing factors
old_cat3_logic = '''                if fuel_key == "electricity":
                    # T&D losses for electricity
                    cat3_emissions = emission_input.amount * cat3_data["td_factor"]
                else:
                    # WTT emissions for fuels
                    cat3_emissions = emission_input.amount * cat3_data["wtt_factor"]'''

new_cat3_logic = '''                if fuel_key == "electricity":
                    # T&D losses for electricity
                    if "td_factor" in cat3_data:
                        cat3_emissions = emission_input.amount * cat3_data["td_factor"]
                else:
                    # WTT emissions for fuels
                    if "wtt_factor" in cat3_data:
                        cat3_emissions = emission_input.amount * cat3_data["wtt_factor"]'''

content = content.replace(old_cat3_logic, new_cat3_logic)

# Write back
with open("app/api/v1/endpoints/ghg_calculator.py", "w") as f:
    f.write(content)

print("✅ Fixed activity type mappings and Category 3 logic")