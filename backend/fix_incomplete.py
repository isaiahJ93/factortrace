# fix_incomplete_if.py
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find and fix the incomplete if statement around line 848
for i in range(845, min(855, len(lines))):
    if 'if not data.get(\'transition_plan_explanation\'):' in lines[i]:
        # Add a pass statement to complete it
        if i + 1 < len(lines) and not lines[i + 1].strip().startswith('pass'):
            lines.insert(i + 1, '            pass\n')
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed incomplete if statement")
