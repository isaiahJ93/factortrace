# Read api.py
with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Add debug logging after the import
content = content.replace(
    'from app.api.v1.endpoints import verify_voucher',
    '''from app.api.v1.endpoints import verify_voucher
logger.info(f"✅ Imported verify_voucher module: {verify_voucher}")
logger.info(f"✅ Verify router: {verify_voucher.router}")'''
)

# Write back
with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("✅ Added debug logging")
