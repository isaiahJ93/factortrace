#!/usr/bin/env python3
import re

# Check the router definition in esrs_e1_full.py
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Look for router definition with prefix
if 'router = APIRouter(prefix="/esrs/e1"' in content:
    print("Found double prefix issue!")
    # Remove the prefix from the router
    content = re.sub(
        r'router = APIRouter\(prefix="/esrs/e1"[^)]*\)',
        'router = APIRouter()',
        content
    )
    
    # Save the file
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
        f.write(content)
    
    print("✅ Removed duplicate prefix from router")
else:
    print("No duplicate prefix found in router definition")

# Now let's check the actual routes
matches = re.findall(r'@router\.(get|post|put|delete)\("([^"]+)"\)', content)
print("\nRoutes in esrs_e1_full.py:")
for method, route in matches:
    print(f"  {method.upper()}: {route}")
