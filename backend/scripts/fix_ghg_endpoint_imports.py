#!/usr/bin/env python3
"""Fix imports in GHG endpoints"""

def fix_imports():
    # Fix ghg_calculations.py
    with open("app/api/v1/endpoints/ghg_calculations.py", "r") as f:
        content = f.read()
    
    # Add the missing import
    if "from app.models.ghg_tables import" not in content:
        # Add after the other imports
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "from app.services.ghg_calculation_service import" in line:
                lines.insert(i+1, "from app.models.ghg_tables import GHGCalculationResult")
                break
        content = '\n'.join(lines)
    
    with open("app/api/v1/endpoints/ghg_calculations.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed imports in ghg_calculations.py")

if __name__ == "__main__":
    fix_imports()
