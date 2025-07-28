with open('app/api/v1/api.py', 'r') as f:
    lines = f.readlines()

# Find where to add the import
import_added = False
webhook_added = False
new_lines = []

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Add import after other endpoint imports
    if 'from .endpoints import voucher' in line and not import_added:
        new_lines.append('from .endpoints import webhook_simple\n')
        import_added = True
    
    # Add endpoint after vouchers
    if 'name="vouchers"' in line:
        # Find the closing of this endpoint
        j = i
        while j < len(lines) and ')' not in lines[j]:
            j += 1
        # Skip to after the closing parenthesis
        while j < len(lines) - 1:
            new_lines.append(lines[j + 1])
            j += 1
            if ')' in lines[j] and not webhook_added:
                new_lines.append('\n# Stripe webhook handler\n')
                new_lines.append('loader.register_endpoint(\n')
                new_lines.append('    name="webhook_simple",\n')
                new_lines.append('    module_path="webhook_simple",\n')
                new_lines.append('    prefix="/vouchers",\n')
                new_lines.append('    tags=["webhook"],\n')
                new_lines.append('    description="Stripe webhook handler"\n')
                new_lines.append(')\n')
                webhook_added = True
                break

with open('app/api/v1/api.py', 'w') as f:
    f.writelines(new_lines)

print(f"Import added: {import_added}")
print(f"Webhook added: {webhook_added}")
