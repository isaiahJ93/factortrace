# Read the file
with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Fix the broken include_router calls
# Remove the duplicate/broken line
content = content.replace(
    '''api_router.include_router(esrs_e1_full.router, prefix="/esrs-e1", tags=["ESRS E1"])
api_router.include_router(
api_router.include_router(verify_voucher.router, prefix="/verify", tags=["voucher"])
    ghg_calculator.router,
    prefix="/ghg-calculator",
    tags=["ghg-calculator"]
)''',
    '''api_router.include_router(esrs_e1_full.router, prefix="/esrs-e1", tags=["ESRS E1"])
api_router.include_router(
    ghg_calculator.router,
    prefix="/ghg-calculator",
    tags=["ghg-calculator"]
)
api_router.include_router(verify_voucher.router, prefix="/verify", tags=["voucher"])''')

# Write back
with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("✅ Fixed router syntax")
