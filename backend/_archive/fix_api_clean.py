with open('app/api/v1/api.py', 'r') as f:
    lines = f.readlines()

# Find and fix the vouchers section
new_lines = []
i = 0
while i < len(lines):
    # Skip the broken vouchers section
    if ('name="vouchers"' in lines[i] or 
        ('loader.register_endpoint(' in lines[i] and i > 140 and i < 160)):
        # Skip until we find the end or next section
        while i < len(lines) and 'AUTHENTICATION & USERS' not in lines[i]:
            i += 1
        # Add the correct vouchers endpoint
        new_lines.extend([
            '# Voucher/Payment system - Critical for revenue\n',
            'loader.register_endpoint(\n',
            '    name="vouchers",\n',
            '    module_path="voucher",\n',
            '    prefix="/vouchers",\n',
            '    tags=["vouchers", "payments"],\n',
            '    critical=True,\n',
            '    description="Voucher management and Stripe checkout"\n',
            ')\n',
            '\n'
        ])
    else:
        new_lines.append(lines[i])
        i += 1

with open('app/api/v1/api.py', 'w') as f:
    f.writelines(new_lines)

print("Fixed API file completely")
