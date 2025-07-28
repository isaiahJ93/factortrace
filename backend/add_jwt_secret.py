import re

# Read the config file
with open('app/core/config.py', 'r') as f:
    content = f.read()

# Find the Settings class and add jwt_secret field
# Look for class Settings and add the field after other string fields
pattern = r'(class Settings.*?:\s*\n)(.*?)(\n\s*@)'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Find a good place to add jwt_secret (after other secret fields or string fields)
    class_content = match.group(2)
    
    # Try to find where other secrets are defined
    if 'secret' in class_content.lower():
        # Add after the last secret field
        content = re.sub(
            r'(secret[^=]*=\s*[^\n]+)',
            r'\1\n    jwt_secret: str = Field(default="", env="JWT_SECRET")',
            content
        )
    else:
        # Add after the first string field
        content = re.sub(
            r'(class Settings[^:]*:.*?\n\s+)(\w+:\s*str[^\n]+)',
            r'\1\2\n    jwt_secret: str = Field(default="", env="JWT_SECRET")',
            content,
            count=1,
            flags=re.DOTALL
        )
else:
    # Simpler approach - find any field definition and add after it
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'class Settings' in line:
            # Find the first field definition after class Settings
            for j in range(i+1, min(i+20, len(lines))):
                if ': str' in lines[j] or ': Optional[str]' in lines[j]:
                    # Add jwt_secret after this line
                    indent = len(lines[j]) - len(lines[j].lstrip())
                    lines.insert(j+1, ' ' * indent + 'jwt_secret: str = Field(default="", env="JWT_SECRET")')
                    break
            break
    content = '\n'.join(lines)

# Write back
with open('app/core/config.py', 'w') as f:
    f.write(content)

print("✅ Added jwt_secret to Settings class")
