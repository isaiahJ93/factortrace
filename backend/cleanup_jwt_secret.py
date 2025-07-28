# Read the file
with open('app/core/config.py', 'r') as f:
    lines = f.readlines()

# Keep only the jwt_secret inside the Settings class
# Remove any jwt_secret lines that are in the wrong place
cleaned_lines = []
inside_settings_class = False
settings_indent = 0

for i, line in enumerate(lines):
    if 'class Settings(BaseSettings):' in line:
        inside_settings_class = True
        settings_indent = len(line) - len(line.lstrip())
    elif inside_settings_class and line.strip() and not line.startswith(' '):
        # We've left the Settings class
        inside_settings_class = False
    
    # Keep the line if it's the correct jwt_secret or not a jwt_secret line
    if 'jwt_secret:' in line:
        # Only keep if it's inside Settings class and properly indented
        if inside_settings_class and len(line) - len(line.lstrip()) == settings_indent + 4:
            cleaned_lines.append(line)
        # Skip any other jwt_secret lines
    else:
        cleaned_lines.append(line)

# Write back
with open('app/core/config.py', 'w') as f:
    f.writelines(cleaned_lines)

print("✅ Cleaned up misplaced jwt_secret lines")
