#!/usr/bin/env python3
"""Fix datetime import conflicts and usage"""

import re

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

print("Fixing datetime import conflicts and usage...")

# Fix 1: Replace problematic import pattern
content = content.replace(
    'from datetime import date, datetime as dt',
    'from datetime import date, datetime as dt, timezone'
)

# Fix 2: Replace datetime.utcnow() with correct form
fixes = [
    # Module method calls that should use the class
    (r'\bdatetime\.utcnow\(\)', 'dt.utcnow()'),
    (r'\bdatetime\.now\(\)', 'dt.now()'),
    (r'\bdatetime\.strptime\(', 'dt.strptime('),
    (r'\bdatetime\.strftime\(', 'dt.strftime('),
    (r'\bdatetime\.fromisoformat\(', 'dt.fromisoformat('),
    (r'\bdatetime\.combine\(', 'dt.combine('),
    
    # Fix datetime.datetime patterns (double datetime)
    (r'\bdatetime\.datetime\.now\(\)', 'dt.now()'),
    (r'\bdatetime\.datetime\.utcnow\(\)', 'dt.utcnow()'),
    (r'\bdatetime\.datetime\.strptime\(', 'dt.strptime('),
    (r'\bdatetime\.datetime\.fromisoformat\(', 'dt.fromisoformat('),
]

fix_count = 0
for pattern, replacement in fixes:
    matches = len(re.findall(pattern, content))
    if matches > 0:
        content = re.sub(pattern, replacement, content)
        fix_count += matches
        print(f"  Fixed {matches} instances of {pattern}")

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print(f"\n✅ Fixed {fix_count} datetime usage issues")
