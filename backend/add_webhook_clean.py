with open('app/api/v1/api.py', 'r') as f:
    lines = f.readlines()

# Find where to add webhook after vouchers
new_lines = []
i = 0
while i < len(lines):
    new_lines.append(lines[i])
    
    # Look for the vouchers endpoint
    if 'name="vouchers"' in lines[i] and 'loader.register_endpoint' in lines[i-1] if i > 0 else False:
        # Find the end of this endpoint block
        paren_count = 1
        i += 1
        while i < len(lines) and paren_count > 0:
            new_lines.append(lines[i])
            paren_count += lines[i].count('(') - lines[i].count(')')
            i += 1
        
        # Add webhook endpoint after vouchers
        new_lines.append('\n')
        new_lines.append('# Webhook endpoint for Stripe\n')
        new_lines.append('loader.register_endpoint(\n')
        new_lines.append('    name="webhook",\n')
        new_lines.append('    module_path="webhook",\n')
        new_lines.append('    prefix="/vouchers",\n')
        new_lines.append('    tags=["webhook"],\n')
        new_lines.append('    description="Stripe webhook handler"\n')
        new_lines.append(')\n')
        continue
    
    i += 1

# Write the fixed content
with open('app/api/v1/api.py', 'w') as f:
    f.writelines(new_lines)

print("Added webhook endpoint cleanly")

# Also make sure webhook is imported
with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

if 'from .endpoints import webhook' not in content:
    content = content.replace(
        'from .endpoints import voucher',
        'from .endpoints import voucher\nfrom .endpoints import webhook'
    )
    
    with open('app/api/v1/api.py', 'w') as f:
        f.write(content)
    print("Added webhook import")
