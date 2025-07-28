#!/usr/bin/env python3
"""Fix UUID handling for SQLite"""

def fix_uuid_handling():
    # Fix the calculation service
    with open("app/services/ghg_calculation_service.py", "r") as f:
        content = f.read()
    
    # Replace uuid4() with str(uuid4())
    content = content.replace(
        "id=uuid4(),",
        "id=str(uuid4()),"
    )
    
    # Fix organization_id conversion
    content = content.replace(
        "organization_id=request.organization_id,",
        "organization_id=str(request.organization_id),"
    )
    
    # Fix calculation_id assignment
    content = content.replace(
        "calculation_id=calculation.id,",
        "calculation_id=str(calculation.id),"
    )
    
    with open("app/services/ghg_calculation_service.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed UUID handling in calculation service")
    
    # Also fix the populate script
    with open("scripts/populate_ghg_data_fixed.py", "r") as f:
        content = f.read()
    
    # Ensure org_id is a string
    content = content.replace(
        'org_id = "12345678-1234-5678-1234-567812345678"',
        'org_id = "12345678-1234-5678-1234-567812345678"  # String for SQLite'
    )
    
    with open("scripts/populate_ghg_data_fixed.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed UUID handling in populate script")

if __name__ == "__main__":
    fix_uuid_handling()
