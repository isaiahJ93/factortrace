# Read api.py
with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Find where to add the router inclusion
# Look for the last api_router.include_router line
import re

# Find all include_router lines
includes = list(re.finditer(r'api_router\.include_router\([^)]+\)', content))

if includes:
    # Get the position after the last include
    last_include = includes[-1]
    insert_pos = last_include.end()
    
    # Add the verify router inclusion
    new_line = '\napi_router.include_router(verify_voucher.router, prefix="/verify", tags=["voucher"])'
    content = content[:insert_pos] + new_line + content[insert_pos:]
else:
    # If no includes found, add after api_router = APIRouter()
    router_pos = content.find('api_router = APIRouter()')
    if router_pos != -1:
        insert_pos = content.find('\n', router_pos) + 1
        new_line = 'api_router.include_router(verify_voucher.router, prefix="/verify", tags=["voucher"])\n'
        content = content[:insert_pos] + new_line + content[insert_pos:]

# Write back
with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("✅ Added verify_voucher router to api_router")
