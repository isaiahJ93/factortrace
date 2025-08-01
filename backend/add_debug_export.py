# Add to your esrs_e1_full.py temporarily for debugging

import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Add logging at the start of export_ixbrl
debug_code = '''
    logger.info(f"=== iXBRL Export Called ===")
    logger.info(f"Received data keys: {list(data.keys())}")
    logger.info(f"Entity name: {data.get('entity_name', 'Not provided')}")
'''

# Find the export_ixbrl function and add logging
pattern = r'(async def export_ixbrl.*?:\n\s*""".*?"""\n)'
replacement = r'\1' + debug_code

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Added debug logging to export_ixbrl")
