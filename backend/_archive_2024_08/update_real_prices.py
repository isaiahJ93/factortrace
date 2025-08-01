import re

# Your real Stripe price IDs
PRICE_IDS = {
    'single': 'price_1Rkh4iDuhtIL48LYDzQ4naW7',      # €950
    'bundle-8': 'price_1Rkh5JDuhtIL48LYrVFkNMLN',    # €5,000
    'bundle-20': 'price_1Rkh6BDuhtIL48LYZFerFW52',   # €10,000
    'bundle-50': 'price_1Rkh6iDuhtIL48LYC3stXrV0'    # €15,000
}

with open('app/api/v1/endpoints/voucher.py', 'r') as f:
    content = f.read()

# Update the PRICE_IDS dictionary
new_price_ids = f"""PRICE_IDS = {{
    'single': '{PRICE_IDS['single']}',      # €950
    'bundle-8': '{PRICE_IDS['bundle-8']}',    # €5,000
    'bundle-20': '{PRICE_IDS['bundle-20']}',   # €10,000
    'bundle-50': '{PRICE_IDS['bundle-50']}'    # €15,000
}}"""

# Replace the PRICE_IDS section
content = re.sub(r'PRICE_IDS = \{[^}]+\}', new_price_ids, content, flags=re.DOTALL)

# Also update check to remove XXXXX check since we have real IDs now
content = content.replace(
    "if not stripe.api_key or 'YOUR_ACTUAL' in str(stripe.api_key) or 'XXXXX' in price_id:",
    "if not stripe.api_key or 'YOUR_ACTUAL' in str(stripe.api_key):"
)

with open('app/api/v1/endpoints/voucher.py', 'w') as f:
    f.write(content)

print("✅ Updated with real Stripe price IDs!")
for key, price_id in PRICE_IDS.items():
    print(f"{key}: {price_id}")
