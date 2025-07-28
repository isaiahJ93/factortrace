import re

# Your real Stripe price IDs
REAL_PRICE_IDS = {
    'single': 'price_1Rkh4iDuhtIL48LYDzQ4naW7',      # €950
    'bundle-8': 'price_1Rkh5JDuhtIL48LYrVFkNMLN',    # €5,000
    'bundle-20': 'price_1Rkh6BDuhtIL48LYZFerFW52',   # €10,000
    'bundle-50': 'price_1Rkh6iDuhtIL48LYC3stXrV0'    # €15,000
}

with open('app/api/v1/endpoints/voucher.py', 'r') as f:
    content = f.read()

# Replace any old SINGLE_PRICE_ID constant
content = re.sub(
    r'SINGLE_PRICE_ID = "[^"]*"',
    f'SINGLE_PRICE_ID = "{REAL_PRICE_IDS["single"]}"',
    content
)

# Update PRICE_IDS dictionary
new_price_ids = f"""PRICE_IDS = {{
    'single': '{REAL_PRICE_IDS['single']}',      # €950
    'bundle-8': '{REAL_PRICE_IDS['bundle-8']}',    # €5,000
    'bundle-20': '{REAL_PRICE_IDS['bundle-20']}',   # €10,000
    'bundle-50': '{REAL_PRICE_IDS['bundle-50']}'    # €15,000
}}"""

content = re.sub(r'PRICE_IDS = \{[^}]+\}', new_price_ids, content, flags=re.DOTALL)

# Make sure we're using PRICE_IDS in the checkout function
# Find the line where price_id is set
if "price_id = PRICE_IDS.get" not in content:
    # Need to add logic to get price from dict
    content = re.sub(
        r"'price': [^,]+,",
        "'price': PRICE_IDS.get(request.package_type, PRICE_IDS['single']),",
        content
    )

with open('app/api/v1/endpoints/voucher.py', 'w') as f:
    f.write(content)

print("✅ Fixed price IDs!")
print("Updated prices:")
for key, price_id in REAL_PRICE_IDS.items():
    print(f"  {key}: {price_id}")
