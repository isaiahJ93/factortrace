# Read the file
with open('app/core/config.py', 'r') as f:
    lines = f.readlines()

# Find the Settings class and add jwt_secret after other fields
settings_found = False
for i, line in enumerate(lines):
    if 'class Settings(BaseSettings):' in line:
        settings_found = True
    elif settings_found and 'log_level: str = Field' in line:
        # Add jwt_secret after log_level
        indent = '    '  # 4 spaces to match class indentation
        lines.insert(i + 1, f'{indent}jwt_secret: str = Field(default="", env="JWT_SECRET")\n')
        break

# Write back
with open('app/core/config.py', 'w') as f:
    f.writelines(lines)

print("✅ Moved jwt_secret inside Settings class")
