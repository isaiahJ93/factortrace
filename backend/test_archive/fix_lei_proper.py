with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Fix lines 12393-12395
if len(lines) > 12394:
    # Line 12394 (index 12393) - properly indent the raise statement
    lines[12393] = '            raise ValueError(f"Invalid LEI checksum: {lei}")\n'
    
    # Remove or fix line 12395 if it exists
    if len(lines) > 12394 and '# Temporarily disabled' in lines[12394]:
        lines[12394] = ''  # Remove the comment line

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("Fixed LEI validation indentation")
