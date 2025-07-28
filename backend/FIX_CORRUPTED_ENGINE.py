#!/usr/bin/env python3
"""Fix the corrupted create_engine block"""

print("🔧 FIXING CORRUPTED CREATE_ENGINE BLOCK...")

# Read the file
with open('app/core/database.py', 'r') as f:
    content = f.read()

# Find and replace the entire create_engine section
import re

# Pattern to find the corrupted create_engine block
pattern = r'engine = create_engine\([^)]*\)[^)]*\)'

# Replace with a clean version
replacement = '''engine = create_engine(
    str(settings.database_url),
    connect_args={"check_same_thread": False} if is_sqlite else {},
    poolclass=NullPool if is_sqlite else None,
    echo=settings.debug
)'''

# Apply the fix
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('app/core/database.py', 'w') as f:
    f.write(content)

print("✅ Fixed create_engine block!")
print("\n🚀 Now run: uvicorn app.main:app --reload --port 8000")