#!/usr/bin/env python3

# Read the file
with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Fix the broken include_router call
# Replace the malformed section
broken_pattern = '''api_router.include_router(esrs_e1_full.router, prefix="/esrs-e1", tags=["ESRS E1"])
    ghg_calculator.router,
    prefix="/ghg-calculator",
    tags=["ghg-calculator"]
)'''

fixed_pattern = '''api_router.include_router(esrs_e1_full.router, prefix="/esrs-e1", tags=["ESRS E1"])
api_router.include_router(
    ghg_calculator.router,
    prefix="/ghg-calculator",
    tags=["ghg-calculator"]
)'''

content = content.replace(broken_pattern, fixed_pattern)

# Save the fixed file
with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("✅ Fixed broken include_router call")

# Verify it's valid Python
try:
    compile(content, 'app/api/v1/api.py', 'exec')
    print("✅ File is valid Python")
except Exception as e:
    print(f"❌ Error: {e}")
