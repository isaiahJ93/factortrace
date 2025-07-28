# Read api.py
with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Add import if not exists
if 'verify_voucher' not in content:
    # Find the last import from endpoints
    import_section = content.split('api_router = APIRouter()')[0]
    
    # Add the import
    new_import = "from app.api.v1.endpoints import verify_voucher\n"
    content = content.replace('api_router = APIRouter()', 
                              new_import + '\napi_router = APIRouter()')
    
    # Find where routers are included and add verify_voucher
    if 'api_router.include_router(' in content:
        # Find the last include_router
        lines = content.split('\n')
        for i in range(len(lines)-1, -1, -1):
            if 'api_router.include_router(' in lines[i]:
                # Add after this line
                lines.insert(i+1, 'api_router.include_router(verify_voucher.router, prefix="/verify", tags=["voucher"])')
                break
        content = '\n'.join(lines)

# Write back
with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("✅ Added verify_voucher to api.py")
