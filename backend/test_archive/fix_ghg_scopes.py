with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find the GHG_SCOPES line
for i, line in enumerate(lines):
    if line.strip() == 'GHG_SCOPES = {':
        # Replace with a complete dictionary
        lines[i] = '''GHG_SCOPES = {
    'scope1': 'Direct GHG emissions',
    'scope2': 'Indirect GHG emissions from purchased energy',
    'scope3': 'Other indirect GHG emissions'
}
'''
        break

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed GHG_SCOPES")
