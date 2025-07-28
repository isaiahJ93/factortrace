#!/usr/bin/env python3
"""Complete fix for UUID handling in SQLite"""

def fix_all_uuid_issues():
    # Fix the calculation service completely
    with open("app/services/ghg_calculation_service.py", "r") as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        # Fix uuid4() calls
        if "uuid4()" in line and "import" not in line:
            line = line.replace("uuid4()", "str(uuid4())")
        
        # Fix request.organization_id
        if "organization_id=request.organization_id" in line:
            line = line.replace(
                "organization_id=request.organization_id",
                "organization_id=str(request.organization_id)"
            )
        
        # Fix calculation.id references
        if "calculation_id=calculation.id" in line:
            line = line.replace(
                "calculation_id=calculation.id",
                "calculation_id=str(calculation.id) if calculation.id else None"
            )
        
        new_lines.append(line)
    
    with open("app/services/ghg_calculation_service.py", "w") as f:
        f.writelines(new_lines)
    
    print("✅ Fixed UUID handling in calculation service")

if __name__ == "__main__":
    fix_all_uuid_issues()
