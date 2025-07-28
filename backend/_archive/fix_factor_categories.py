import re

with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    content = f.read()

# Find the mock_factors section and update it
mock_factors_new = '''    mock_factors = [
        {
            "id": 1,
            "name": "Natural Gas",
            "category": "fuel_energy_activities",
            "unit": "m³",
            "factor": 0.18454,
            "source": "EPA",
            "scope": 1
        },
        {
            "id": 2,
            "name": "Electricity - Grid Average",
            "category": "fuel_energy_activities", 
            "unit": "kWh",
            "factor": 0.435,
            "source": "EPA eGRID",
            "scope": 2
        },
        {
            "id": 3,
            "name": "Air Travel (Economy)",
            "category": "business_travel",
            "unit": "passenger-km",
            "factor": 0.223,
            "source": "EPA",
            "scope": 3
        },
        {
            "id": 4,
            "name": "Rail Travel",
            "category": "business_travel",
            "unit": "passenger-km", 
            "factor": 0.041,
            "source": "EPA",
            "scope": 3
        },
        {
            "id": 5,
            "name": "Waste to Landfill",
            "category": "waste_operations",
            "unit": "tonnes",
            "factor": 467.0,
            "source": "EPA",
            "scope": 3
        },
        {
            "id": 6,
            "name": "Purchased Steel",
            "category": "purchased_goods_services",
            "unit": "kg",
            "factor": 1.85,
            "source": "EPA",
            "scope": 3
        },
        {
            "id": 7,
            "name": "Hotel Stay",
            "category": "business_travel",
            "unit": "nights",
            "factor": 15.3,
            "source": "EPA",
            "scope": 3
        },
        {
            "id": 8,
            "name": "Employee Commuting - Car",
            "category": "employee_commuting",
            "unit": "km",
            "factor": 0.171,
            "source": "EPA",
            "scope": 3
        }
    ]'''

# Replace the mock_factors section
pattern = r'mock_factors = \[(.*?)\]'
content = re.sub(pattern, mock_factors_new, content, flags=re.DOTALL)

with open('app/api/v1/endpoints/emission_factors.py', 'w') as f:
    f.write(content)

print("Updated emission factors with categories")
