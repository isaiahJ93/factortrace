import re

# Read the main.py file
with open('app/main.py', 'r') as f:
    content = f.read()

# Add import if not exists
if 'verify_voucher' not in content:
    # Find the last import from app.api
    import_pattern = r'(from app\.api\..*import.*\n)'
    imports = re.findall(import_pattern, content)
    if imports:
        last_import = imports[-1]
        new_import = last_import + "from app.api.verify_voucher import router as verify_router\n"
        content = content.replace(last_import, new_import)

# Add router registration after emissions_router
if 'verify_router' not in content:
    emissions_line = 'app.include_router(emissions_router, prefix="/api/v1/emissions", tags=["emissions"])'
    if emissions_line in content:
        new_line = emissions_line + '\n    app.include_router(verify_router, prefix="/api/v1", tags=["voucher"])'
        content = content.replace(emissions_line, new_line)

# Write back
with open('app/main.py', 'w') as f:
    f.write(content)

print("✅ Added verify_voucher router to main.py")
