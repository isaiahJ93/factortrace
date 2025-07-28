with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Remove ALL webhook-related content and orphaned lines
import re

# Remove webhook endpoints
content = re.sub(r'# Webhook endpoint.*?description="Stripe webhook handler"\s*\)', '', content, flags=re.DOTALL)

# Remove orphaned module_path line
content = re.sub(r'\n\s*module_path="voucher",\s*\n', '\n', content)

# Clean up multiple newlines
content = re.sub(r'\n\n\n+', '\n\n', content)

with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("Removed all webhook entries and cleaned up")
