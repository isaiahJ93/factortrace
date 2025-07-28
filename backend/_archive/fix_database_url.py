#!/usr/bin/env python3
"""Direct fix for database URL issue"""

# Fix database.py
with open('app/core/database.py', 'r') as f:
    content = f.read()

# Replace SQLALCHEMY_DATABASE_URL with database_url and convert to string
content = content.replace('settings.SQLALCHEMY_DATABASE_URL', 'str(settings.database_url)')

# Also fix any other occurrences where we need string conversion
content = content.replace('is_sqlite = str(str(settings.database_url))', 'is_sqlite = str(settings.database_url)')  # Avoid double str()

with open('app/core/database.py', 'w') as f:
    f.write(content)

print("✅ Fixed database.py")
print("\n🚀 Now run: uvicorn app.main:app --reload --port 8000")