with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Fix lines 1009-1010 (0-indexed: 1008-1009)
for i in range(len(lines)):
    if 'logger.info(f"Scope3 breakdown received:' in lines[i]:
        # Add proper indentation (8 spaces to match surrounding code)
        lines[i] = '        ' + lines[i].lstrip()
    elif 'logger.info(f"Scope3 breakdown keys:' in lines[i]:
        lines[i] = '        ' + lines[i].lstrip()

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed logger indentation")
