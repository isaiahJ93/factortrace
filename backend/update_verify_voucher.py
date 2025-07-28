# Read the file
with open('app/api/v1/endpoints/verify_voucher.py', 'r') as f:
    content = f.read()

# Replace os.getenv with settings
content = content.replace(
    "import os",
    "import os\nfrom app.core.config import settings"
)

content = content.replace(
    "jwt_secret = os.getenv('JWT_SECRET', '')",
    "jwt_secret = settings.jwt_secret"
)

# Write back
with open('app/api/v1/endpoints/verify_voucher.py', 'w') as f:
    f.write(content)

print("✅ Updated to use settings.jwt_secret")
