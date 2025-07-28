# Read the file
with open('app/main.py', 'r') as f:
    lines = f.readlines()

# Find and fix the problematic section around line 264
for i in range(len(lines)):
    if i >= 262 and i <= 270:
        # Fix the structure
        if lines[i].strip() == 'from app.api.v1.api import api_router':
            # This should be inside the try block
            lines[i] = ''  # Remove this line
        elif lines[i].strip() == 'try:':
            # Add the import after try:
            lines[i] = 'try:\n    from app.api.v1.api import api_router\n'

# Write back
with open('app/main.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed try block indentation")
