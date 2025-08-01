import re

# Read main.py
with open('app/main.py', 'r') as f:
    content = f.read()

# Find where api_router is included
import_pos = content.find('app.include_router(api_router')
if import_pos == -1:
    print("Could not find api_router include")
    exit(1)

# Find the end of that line
end_pos = content.find('\n', import_pos)

# Insert emissions router right after
insert_code = '''

# EMERGENCY FIX - Direct emissions router include
try:
    from app.api.v1.endpoints.emissions import router as emissions_router
    app.include_router(emissions_router, prefix="/api/v1/emissions", tags=["emissions"])
    logger.info("✅ Emissions router manually included")
except Exception as e:
    logger.error(f"❌ Failed to include emissions router: {e}")
'''

# Insert the code
new_content = content[:end_pos] + insert_code + content[end_pos:]

# Write back
with open('app/main.py', 'w') as f:
    f.write(new_content)

print("✅ Fixed main.py - emissions router added")
