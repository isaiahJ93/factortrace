# Read main.py
with open('app/main.py', 'r') as f:
    content = f.read()

# Add debug logging after the router registration
content = content.replace(
    'app.include_router(verify_router, prefix="/api/v1", tags=["voucher"])',
    '''app.include_router(verify_router, prefix="/api/v1", tags=["voucher"])
    logger.info(f"✅ Verify router registered at /api/v1")
    logger.info(f"Available routes: {[route.path for route in app.routes]}")'''
)

# Write back
with open('app/main.py', 'w') as f:
    f.write(content)

print("✅ Added debug logging")
