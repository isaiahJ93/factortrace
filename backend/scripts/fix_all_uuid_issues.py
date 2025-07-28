#!/usr/bin/env python3
"""Fix all UUID issues for SQLite"""

def fix_calculation_service():
    with open("app/services/ghg_calculation_service.py", "r") as f:
        content = f.read()
    
    # Fix the GHGActivityData creation
    # Find the line that creates activity_db
    content = content.replace(
        "activity_db = GHGActivityData(",
        "activity_db = GHGActivityData(\n                id=str(uuid4()),"
    )
    
    # Also fix GHGCategoryResult creation
    content = content.replace(
        "category_result = GHGCategoryResult(",
        "category_result = GHGCategoryResult(\n                id=str(uuid4()),"
    )
    
    # Ensure we're importing uuid4
    if "from uuid import uuid4" not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "from uuid import" in line:
                lines[i] = "from uuid import UUID, uuid4"
                break
            elif "import uuid" in line:
                lines.insert(i+1, "from uuid import uuid4")
                break
        content = '\n'.join(lines)
    
    with open("app/services/ghg_calculation_service.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed UUID issues in calculation service")

if __name__ == "__main__":
    fix_calculation_service()
