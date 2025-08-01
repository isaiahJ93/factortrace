with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find get_enhanced_namespaces function at line 143
insert_pos = None
for i, line in enumerate(lines):
    if 'def get_enhanced_namespaces' in line and i >= 142:
        # Find the end of the function
        j = i + 1
        while j < len(lines) and not lines[j].startswith('def '):
            j += 1
        insert_pos = j
        break

if insert_pos:
    new_function = '''
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

'''
    lines.insert(insert_pos, new_function)
    
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Added get_namespace_map function")
