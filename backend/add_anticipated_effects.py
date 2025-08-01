# add_anticipated_effects_fixed.py
import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find the extract_financial_effects_data function and add anticipated_effects
pattern = r"('future_period_effects': financial_effects\.get\('future_period_effects', {}\))"
replacement = r"\1,\n        'anticipated_effects': financial_effects.get('anticipated_effects', {\n            'short_term': {},\n            'medium_term': {},\n            'long_term': {}\n        })"

content = re.sub(pattern, replacement, content)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Added anticipated_effects to financial data extraction")