with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Add import if not present
if 'from .endpoints import webhook_simple' not in content:
    import_line = 'from .endpoints import voucher'
    content = content.replace(import_line, import_line + '\nfrom .endpoints import webhook_simple')

# Add the endpoint registration after vouchers
if 'webhook_simple' not in content:
    voucher_end = content.find('name="vouchers"')
    if voucher_end > 0:
        # Find the end of the vouchers registration
        closing_paren = content.find(')', voucher_end)
        insert_pos = content.find('\n', closing_paren) + 1
        
        webhook_registration = '''
# Stripe webhook handler
loader.register_endpoint(
    name="webhook_simple",
    module_path="webhook_simple",
    prefix="/vouchers",
    tags=["webhook"],
    description="Stripe webhook handler"
)
'''
        content = content[:insert_pos] + webhook_registration + content[insert_pos:]

with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("Added webhook to API")
