with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Fix the broken vouchers endpoint
content = content.replace(
    '''loader.register_endpoint(
    name="vouchers",
# Stripe webhook handler
loader.register_endpoint(
    name="webhook_simple",
    module_path="webhook_simple",
    prefix="/vouchers",
    tags=["webhook"],
    description="Stripe webhook handler"
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

# Remove any remaining webhook references
import re
content = re.sub(r'# Stripe webhook handler\s*', '', content)

with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("Fixed vouchers endpoint")
