import re

with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Remove all webhook endpoint attempts first
content = re.sub(r'# Webhook endpoint.*?loader\.register_endpoint\([^)]+name="webhook"[^)]+\)\s*', '', content, flags=re.DOTALL)

# Also remove any orphaned lines
content = re.sub(r'\n\s*module_path="voucher",\s*\n', '\n', content)
content = re.sub(r'\n\s*module_path="webhook",\s*\n', '\n', content)

# Now add webhook properly after vouchers
# Find the vouchers endpoint
voucher_match = re.search(r'(loader\.register_endpoint\(\s*name="vouchers"[^)]+\))', content, re.DOTALL)

if voucher_match:
    # Insert webhook after vouchers
    end_pos = voucher_match.end()
    webhook_code = '''

# Webhook endpoint for Stripe payments
loader.register_endpoint(
    name="webhook",
    module_path="webhook", 
    prefix="/vouchers",
    tags=["webhook"],
    description="Stripe webhook handler"
)'''
    
    content = content[:end_pos] + webhook_code + content[end_pos:]

# Make sure webhook is imported
if 'from .endpoints import webhook' not in content:
    # Find the import section for endpoints
    import_match = re.search(r'(from \.endpoints import.*?)(?=\n\n|\nfrom|\n#)', content, re.DOTALL)
    if import_match:
        imports = import_match.group(1)
        if 'webhook' not in imports:
            content = content.replace(imports, imports + '\nfrom .endpoints import webhook')

# Clean up any multiple blank lines
content = re.sub(r'\n\n\n+', '\n\n', content)

with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("Fixed API file - removed duplicates and fixed formatting")
