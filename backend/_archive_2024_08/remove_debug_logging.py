with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Remove any logger.info lines we added
filtered_lines = []
for line in lines:
    if 'logger.info(f"Scope3 breakdown' not in line and 'logger.info(f"Emissions data:' not in line:
        filtered_lines.append(line)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(filtered_lines)

print("✅ Removed debug logging")
