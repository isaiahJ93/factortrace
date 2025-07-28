import re

# Read the file
with open('app/main.py', 'r') as f:
    content = f.read()

# Fix the broken try block around line 260-270
content = re.sub(
    r'try:\s*\n\s*from app\.api\.v1\.api import api_router\s*\nfrom app\.api\.verify_voucher import router as verify_router',
    'try:\n    from app.api.v1.api import api_router',
    content
)

# Add the verify_voucher import in the existing try block around line 107-112
content = re.sub(
    r'(from app\.api\.v1\.endpoints\.emissions import router as emissions_router\s*\n\s*app\.include_router\(emissions_router[^\n]+\))',
    r'\1\n    from app.api.verify_voucher import router as verify_router\n    app.include_router(verify_router, prefix="/api/v1", tags=["voucher"])',
    content
)

# Write back
with open('app/main.py', 'w') as f:
    f.write(content)

print("✅ Fixed imports in main.py")
