import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Fix the except block indentation - it should be at same level as try
content = re.sub(r'\n        except Exception as e:', r'\n    except Exception as e:', content)
content = re.sub(r'\n            logger\.error\(f"Error in iXBRL structure creation: \{e\}"\)', 
                 r'\n        logger.error(f"Error in iXBRL structure creation: {e}")', content)
content = re.sub(r'\n            raise', r'\n        raise', content)

# Fix any head = ET.SubElement lines that are incorrectly indented
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'head = ET.SubElement(root, \'head\')' in line and not line.startswith('    head = '):
        lines[i] = '    ' + line.strip()

content = '\n'.join(lines)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("Fixed!")
