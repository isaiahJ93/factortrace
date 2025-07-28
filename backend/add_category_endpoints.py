# Check if we need to add category endpoints
import re

with open('app/api/v1/endpoints/emissions.py', 'r') as f:
    content = f.read()

# Add the missing endpoints
if '@router.get("/categories")' not in content:
    # Find a good place to insert (after imports)
    insert_pos = content.find('@router.post("/upload-evidence")')
    
    new_endpoints = '''
@router.get("/categories")
async def get_emission_categories(
    scope: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get emission categories - redirect to emission-factors endpoint"""
    # For now, return mock data to get the frontend working
    if scope == 3:
        return list(SCOPE3_CATEGORIES.keys())
    return ["Fuel & Energy Activities", "Transportation", "Waste", "Other"]

@router.get("/factors")
async def get_emission_factors(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get emission factors for a category"""
    # Mock data to get frontend working
    return [
        {"id": 1, "name": "Electricity", "unit": "kWh", "factor": 0.233},
        {"id": 2, "name": "Natural Gas", "unit": "m³", "factor": 2.02},
        {"id": 3, "name": "Diesel", "unit": "L", "factor": 2.68}
    ]

'''
    
    content = content[:insert_pos] + new_endpoints + '\n' + content[insert_pos:]
    
    with open('app/api/v1/endpoints/emissions.py', 'w') as f:
        f.write(content)
    
    print("Added category endpoints")

