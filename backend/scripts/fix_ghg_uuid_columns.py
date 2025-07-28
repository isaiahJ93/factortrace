#!/usr/bin/env python3
"""Fix UUID columns for SQLite compatibility"""

def fix_uuid_columns():
    with open("app/models/ghg_tables.py", "r") as f:
        content = f.read()
    
    # Replace UUID(as_uuid=True) with a SQLite-compatible version
    # For SQLite, we need to store UUIDs as strings
    
    # Add import for String if not present
    if "from sqlalchemy import" in content and "String" not in content:
        content = content.replace(
            "from sqlalchemy import Column,",
            "from sqlalchemy import Column, String,"
        )
    
    # Replace UUID columns with conditional logic
    uuid_replacement = '''UUID(as_uuid=True) if os.environ.get('DATABASE_URL', '').startswith('postgresql') else String(36)'''
    
    # Check if we need to import os
    if "import os" not in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "import" in line:
                lines.insert(i, "import os")
                break
        content = '\n'.join(lines)
    
    # For now, let's use a simpler approach - just use String(36) for all UUIDs
    content = content.replace("UUID(as_uuid=True)", "String(36)")
    
    with open("app/models/ghg_tables.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed UUID columns for SQLite compatibility")

if __name__ == "__main__":
    fix_uuid_columns()
