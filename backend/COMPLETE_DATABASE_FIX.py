#!/usr/bin/env python3
"""Complete fix for database.py - rewrite the problematic section"""

print("🔧 COMPLETE DATABASE.PY FIX")
print("=========================")

# Read the file
with open('app/core/database.py', 'r') as f:
    lines = f.readlines()

# Find the is_sqlite line
is_sqlite_line = -1
for i, line in enumerate(lines):
    if 'is_sqlite = ' in line and 'str(settings.database_url)' in line:
        is_sqlite_line = i
        break

if is_sqlite_line < 0:
    print("❌ Could not find is_sqlite line!")
    exit(1)

# Keep everything before is_sqlite line + 1
new_content = lines[:is_sqlite_line + 1]

# Add the properly formatted engine creation
engine_block = '''
# Create engine with appropriate configuration
if is_sqlite:
    engine = create_engine(
        str(settings.database_url),
        connect_args={"check_same_thread": False},
        echo=settings.debug
    )
else:
    engine = create_engine(
        str(settings.database_url),
        echo=settings.debug
    )

'''

new_content.append(engine_block)

# Find where to continue (after the corrupted engine block)
continue_from = -1
for i in range(is_sqlite_line + 1, len(lines)):
    if 'SessionLocal' in lines[i] or '@event.listens_for' in lines[i] or 'Base = ' in lines[i]:
        continue_from = i
        break

if continue_from > 0:
    new_content.extend(lines[continue_from:])
else:
    # If we can't find where to continue, just add the rest
    print("⚠️  Warning: Could not find continuation point, appending remaining file")
    new_content.extend(lines[is_sqlite_line + 10:])

# Write the fixed content
with open('app/core/database.py', 'w') as f:
    f.writelines(new_content)

print("✅ Fixed database.py with proper if/else structure!")
print("\n🚀 Now run: uvicorn app.main:app --reload --port 8000")