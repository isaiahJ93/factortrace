# Update emission_factors.py to add capital goods
with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    content = f.read()

# Find the all_factors list and add capital goods items
capital_goods_factors = '''        {"id": 13, "name": "Office Equipment", "category": "capital_goods", "unit": "USD", "factor": 0.65, "source": "EPA", "scope": 3},
        {"id": 14, "name": "Vehicles", "category": "capital_goods", "unit": "USD", "factor": 0.89, "source": "EPA", "scope": 3},
        {"id": 15, "name": "Buildings", "category": "capital_goods", "unit": "m²", "factor": 125.0, "source": "EPA", "scope": 3},
        '''

# Insert before the closing bracket of all_factors
content = content.replace(
    '{"id": 12, "name": "Upstream Fuel Production", "category": "fuel_energy_activities", "unit": "kWh", "factor": 0.045, "source": "EPA", "scope": 3},',
    '{"id": 12, "name": "Upstream Fuel Production", "category": "fuel_energy_activities", "unit": "kWh", "factor": 0.045, "source": "EPA", "scope": 3},\n        ' + capital_goods_factors
)

with open('app/api/v1/endpoints/emission_factors.py', 'w') as f:
    f.write(content)

print("Added capital goods factors")
