import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find the error handler in generate_esrs_e1_xbrl and add traceback
pattern = r'(except Exception as e:.*?logger\.error.*?)"Error generating XBRL report: {str\(e\)}"'
replacement = r'\1"Error generating XBRL report: {str(e)}", exc_info=True'

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Added traceback logging")