# Read the file
with open('app/core/config.py', 'r') as f:
    lines = f.readlines()

# Find and fix the jwt_secret line
for i, line in enumerate(lines):
    if 'jwt_secret:' in line and line.startswith(' '):
        # Count indentation of surrounding lines
        if i > 0:
            # Get indentation from previous line
            prev_line = lines[i-1]
            if prev_line.strip() and not prev_line.strip().startswith('#'):
                indent_count = len(prev_line) - len(prev_line.lstrip())
                # Apply same indentation
                lines[i] = ' ' * indent_count + line.lstrip()
                break

# Write back
with open('app/core/config.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed jwt_secret indentation")
