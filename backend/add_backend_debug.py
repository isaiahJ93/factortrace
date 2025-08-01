import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Add logging in create_scope3_disclosure
pattern = r'(scope3_breakdown = data\.get\(\'scope3_breakdown\', \{\}\))'
replacement = r'''\1
    logger.info(f"Scope3 breakdown received: {scope3_breakdown}")
    logger.info(f"Scope3 breakdown keys: {list(scope3_breakdown.keys()) if scope3_breakdown else 'None'}")'''

content = re.sub(pattern, replacement, content)

# Also add logging for emissions
pattern2 = r'(emissions = data\.get\(\'emissions\', \{\}\))'
replacement2 = r'''\1
    logger.info(f"Emissions data: {emissions}")'''

content = re.sub(pattern2, replacement2, content)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Added debug logging")
