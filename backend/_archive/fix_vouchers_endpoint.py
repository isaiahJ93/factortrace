with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Fix the vouchers endpoint - it's missing module_path
content = content.replace(
    '''loader.register_endpoint(
    name="vouchers",
    prefix="/vouchers",
    tags=["vouchers", "payments"],
    description="Voucher management and Stripe checkout"
)
    prefix="/vouchers",
    tags=["vouchers", "payments"],
    critical=True,
    description="Voucher purchase and redemption system"
)''',
    '''loader.register_endpoint(
    name="vouchers",
    module_path="voucher",
    prefix="/vouchers",
    tags=["vouchers", "payments"],
    critical=True,
    description="Voucher management and Stripe checkout"
)'''
)

with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("Fixed vouchers endpoint")
