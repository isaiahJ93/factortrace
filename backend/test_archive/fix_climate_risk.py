with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find and fix the CLIMATE_RISK_CATEGORIES section
for i in range(len(lines)):
    if 'CLIMATE_RISK_CATEGORIES = {' in lines[i]:
        # Replace the malformed dictionary
        lines[i] = "CLIMATE_RISK_CATEGORIES = {\n"
        lines[i+1] = "    'physical': ['acute', 'chronic'],\n"
        if '}    ' in lines[i+2]:
            lines[i+2] = "    'transition': ['policy', 'technology', 'market', 'reputation']\n"
        lines[i+3] = "}\n"
        # Remove the extra closing brace if it exists
        if lines[i+5].strip() == '}':
            lines[i+5] = ''
        break

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("Fixed CLIMATE_RISK_CATEGORIES structure")
