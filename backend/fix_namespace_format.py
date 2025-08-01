# fix_namespace_format.py
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Add a simple namespace dict right after get_enhanced_namespaces
import re

# Find where to insert
pattern = r'(def get_enhanced_namespaces\(\):.*?}\n)(def )'
replacement = r'''\1
def get_namespace_map():
    """Return namespace map without xmlns: prefix for element creation"""
    return {
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xbrli': 'http://www.xbrl.org/2003/instance',
        'xbrldi': 'http://xbrl.org/2006/xbrldi',
        'xlink': 'http://www.w3.org/1999/xlink',
        'link': 'http://www.xbrl.org/2003/linkbase',
        'iso4217': 'http://www.xbrl.org/2003/iso4217',
        'ix': 'http://www.xbrl.org/2013/inlineXBRL',
        'ixt': 'http://www.xbrl.org/inlineXBRL/transformation/2020-02-12',
        'esrs': 'http://www.efrag.org/esrs/2023',
        'esrs-e1': 'http://www.efrag.org/esrs/2023/e1'
    }

\2'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Update create_schema_references to use get_namespace_map
content = content.replace('namespaces = get_enhanced_namespaces()', 'namespaces = get_namespace_map()')

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed namespace format issue")