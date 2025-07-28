import re

# Read the emissions page
with open('src/app/emissions/new/page.tsx', 'r') as f:
    content = f.read()

# Update the URL to include trailing slash
content = content.replace(
    '/api/v1/emission-factors?scope=',
    '/api/v1/emission-factors/?scope='
)

with open('src/app/emissions/new/page.tsx', 'w') as f:
    f.write(content)

print("Updated frontend to use trailing slash")
