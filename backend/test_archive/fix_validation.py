# fix_validation.py
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find and fix line 2201
for i, line in enumerate(lines):
    if i == 2200:  # Line 2201 (0-indexed)
        # Replace direct key access with .get()
        if "if fe_data['anticipated_effects']:" in line:
            lines[i] = line.replace("if fe_data['anticipated_effects']:", 
                                   "if fe_data.get('anticipated_effects'):")
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed anticipated_effects validation")