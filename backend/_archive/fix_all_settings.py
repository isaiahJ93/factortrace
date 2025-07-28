#!/usr/bin/env python3
"""Fix all settings attributes in database.py"""

import re

# Read database.py
with open('app/core/database.py', 'r') as f:
    content = f.read()

# Apply all fixes
replacements = [
    # Pool settings
    (r'settings\.DB_POOL_SIZE', 'settings.database_pool_size'),
    (r'settings\.DB_MAX_OVERFLOW', 'settings.database_max_overflow'),
    (r'settings\.DB_POOL_TIMEOUT', 'settings.database_pool_timeout'),
    
    # Environment
    (r'settings\.ENVIRONMENT', 'settings.environment'),
    
    # Debug
    (r'settings\.DEBUG', 'settings.debug'),
    
    # If pool_timeout doesn't exist, use default
    (r'pool_timeout=settings\.database_pool_timeout', 'pool_timeout=30'),
]

for old, new in replacements:
    content = re.sub(old, new, content)

# Write back
with open('app/core/database.py', 'w') as f:
    f.write(content)

print("✅ Fixed all settings attributes in database.py")
print("\n🚀 Now run: uvicorn app.main:app --reload --port 8000")