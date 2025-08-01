with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find and fix GHG_SCOPES - it's missing its opening brace
for i, line in enumerate(lines):
    if "'scope1': 'Direct GHG emissions'," in line:
        # Add opening brace before this line
        lines[i] = "GHG_SCOPES = {\n    " + line.strip() + "\n"
        break

# Find and fix ESAP_CONFIG - it's missing 'report_types' key
for i, line in enumerate(lines):
    if "'E1': 'Climate_Change'," in line and 'report_types' not in lines[i-1]:
        # Add the report_types key
        lines[i] = "    'report_types': {\n        " + line.strip() + "\n"
        break

# Find NACE_CODE_REGISTRY and check if it needs fixing
for i, line in enumerate(lines):
    if i >= 55 and i <= 65:
        print(f"Line {i+1}: {line}", end='')

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("\n✅ Fixed dictionary structures")
