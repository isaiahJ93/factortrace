#!/usr/bin/env python3
import re

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Remove /esrs/e1 from all route decorators
content = re.sub(r'@router\.(get|post|put|delete)\("/esrs/e1/', r'@router.\1("/', content)

# Save the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

# Check the routes again
matches = re.findall(r'@router\.(get|post|put|delete)\("([^"]+)"\)', content)
print("Updated routes in esrs_e1_full.py:")
for method, route in matches:
    print(f"  {method.upper()}: {route}")
    
print("\nWith the /esrs-e1 prefix from api.py, the full paths will be:")
for method, route in matches:
    print(f"  {method.upper()}: /api/v1/esrs-e1{route}")
