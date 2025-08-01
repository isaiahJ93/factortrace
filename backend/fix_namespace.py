# fix_namespaces.py
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find the create_schema_references function and add namespaces
import re

# Pattern to find the function
pattern = r'(def create_schema_references\(.*?\):)(.*?)(?=\n    link = ET\.SubElement)'

# Check if get_enhanced_namespaces exists
if 'def get_enhanced_namespaces' in content:
    # Add call to get namespaces
    replacement = r'\1\2\n    namespaces = get_enhanced_namespaces()'
else:
    # Define namespaces inline
    replacement = r'''\1\2
    namespaces = {
        "xbrli": "http://www.xbrl.org/2003/instance",
        "link": "http://www.xbrl.org/2003/linkbase",
        "xlink": "http://www.w3.org/1999/xlink",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "iso4217": "http://www.xbrl.org/2003/iso4217",
        "xbrldi": "http://xbrl.org/2006/xbrldi",
        "ix": "http://www.xbrl.org/2013/inlineXBRL",
        "efrag": "http://www.efrag.org/esrs/2024",
        "esrs": "http://www.efrag.org/esrs/2024/esrs-e1"
    }'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed namespaces in create_schema_references")