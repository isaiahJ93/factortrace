import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find the generate_esrs_e1_xbrl function and add json serialization helper
if 'import json' not in content:
    # Add json import at the top
    content = re.sub(r'(from typing import.*?\n)', r'\1import json\n', content)

# Add a custom JSON encoder if not present
if 'class DateTimeEncoder' not in content:
    encoder_code = '''
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, int):
            return str(obj)
        return super().default(obj)
'''
    # Add after imports
    import_end = content.find('router = APIRouter()')
    content = content[:import_end] + encoder_code + '\n' + content[import_end:]

# Fix the data processing to handle int years
fix_year = '''
    # Ensure reporting_period is a string
    if 'reporting_period' in data and isinstance(data['reporting_period'], int):
        data['reporting_period'] = str(data['reporting_period'])
    if 'year' in data and isinstance(data['year'], int):
        data['year'] = str(data['year'])
'''

# Add this at the start of generate_esrs_e1_xbrl
pattern = r'(async def generate_esrs_e1_xbrl.*?:.*?\n)(.*?)(try:)'
replacement = r'\1\2' + fix_year + '\n    \3'
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Added JSON serialization fixes")
