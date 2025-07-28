import re

# Read the emission_factors.py file
with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    content = f.read()

# Check if the main endpoint exists
if '@router.get("/")' not in content and '@router.get("")' not in content:
    # Find where to insert (after categories endpoint)
    categories_pos = content.find('@router.get("/categories")')
    if categories_pos > 0:
        # Find the end of this function
        next_router = content.find('@router', categories_pos + 1)
        if next_router == -1:
            next_router = len(content)
        
        # Insert the new endpoint
        new_endpoint = '''

@router.get("/")
def get_emission_factors(
    scope: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get emission factors for a specific scope and category"""
    
    # Mock emission factors based on scope and category
    factors = {
        1: [
            {"id": 1, "name": "Natural Gas", "unit": "m³", "factor": 2.02, "scope": 1},
            {"id": 2, "name": "Diesel", "unit": "L", "factor": 2.68, "scope": 1},
            {"id": 3, "name": "Gasoline", "unit": "L", "factor": 2.31, "scope": 1},
        ],
        2: [
            {"id": 4, "name": "Electricity Grid", "unit": "kWh", "factor": 0.233, "scope": 2},
            {"id": 5, "name": "District Heating", "unit": "kWh", "factor": 0.215, "scope": 2},
            {"id": 6, "name": "District Cooling", "unit": "kWh", "factor": 0.198, "scope": 2},
        ],
        3: [
            {"id": 7, "name": "Air Travel (Economy)", "unit": "km", "factor": 0.115, "scope": 3},
            {"id": 8, "name": "Rail Travel", "unit": "km", "factor": 0.041, "scope": 3},
            {"id": 9, "name": "Car Travel", "unit": "km", "factor": 0.171, "scope": 3},
            {"id": 10, "name": "Office Paper", "unit": "kg", "factor": 0.92, "scope": 3},
            {"id": 11, "name": "Plastic Waste", "unit": "kg", "factor": 1.89, "scope": 3},
        ]
    }
    
    if scope:
        return factors.get(scope, [])
    
    # Return all factors if no scope specified
    all_factors = []
    for scope_factors in factors.values():
        all_factors.extend(scope_factors)
    return all_factors
'''
        
        content = content[:next_router] + new_endpoint + '\n' + content[next_router:]
        
        with open('app/api/v1/endpoints/emission_factors.py', 'w') as f:
            f.write(content)
        
        print("Added emission factors endpoint")
    else:
        print("Could not find categories endpoint")
else:
    print("Emission factors endpoint already exists")

