with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Find the vouchers endpoint and fix the webhook addition
lines = content.split('\n')
fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    fixed_lines.append(line)
    
    # If we find the vouchers endpoint closing
    if 'name="vouchers"' in line:
        # Skip ahead to find the closing parenthesis
        while i < len(lines) and ')' not in lines[i]:
            i += 1
            fixed_lines.append(lines[i])
        
        # Add webhook endpoint after vouchers
        if i < len(lines) - 1 and 'webhook' not in lines[i+1]:
            fixed_lines.append('')
            fixed_lines.append('# Webhook endpoint')
            fixed_lines.append('dynamic_router.add_endpoint(')
            fixed_lines.append('    name="webhook",')
            fixed_lines.append('    module_path="webhook",')
            fixed_lines.append('    prefix="/vouchers",')
            fixed_lines.append('    tags=["webhook"],')
            fixed_lines.append('    description="Stripe webhook handler"')
            fixed_lines.append(')')
    
    i += 1

# Write the fixed content
with open('app/api/v1/api.py', 'w') as f:
    f.write('\n'.join(fixed_lines))

print("Fixed API file")
