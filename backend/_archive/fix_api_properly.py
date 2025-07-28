import re

with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Remove any badly added webhook endpoint first
content = re.sub(r'\n*#\s*Webhook endpoint.*?dynamic_router\.add_endpoint\([^)]*\)[^)]*\)', '', content, flags=re.DOTALL)

# Find the vouchers endpoint and ensure it's properly closed
voucher_pattern = r'(dynamic_router\.add_endpoint\(\s*name="vouchers"[^)]+\))'
match = re.search(voucher_pattern, content, re.DOTALL)

if match:
    # Get the position after the vouchers endpoint
    end_pos = match.end()
    
    # Add webhook endpoint properly
    webhook_code = '''

# Webhook endpoint
dynamic_router.add_endpoint(
    name="webhook",
    module_path="webhook",
    prefix="/vouchers",
    tags=["webhook"],
    description="Stripe webhook handler"
)'''
    
    # Insert the webhook code
    content = content[:end_pos] + webhook_code + content[end_pos:]
    
    # Also make sure webhook is imported
    if 'from .endpoints import webhook' not in content:
        # Find the imports section
        import_match = re.search(r'(from \.endpoints import.*?)(\n\n)', content, re.DOTALL)
        if import_match:
            imports = import_match.group(1)
            if 'webhook' not in imports:
                content = content.replace(imports, imports + '\nfrom .endpoints import webhook')

# Write the fixed content
with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("Fixed API file - webhook endpoint added properly")
