with open('app/api/v1/api.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False

for line in lines:
    # Skip webhook_simple registration block
    if 'name="webhook_simple"' in line:
        skip = True
    elif skip and ')' in line:
        skip = False
        continue
    
    if not skip:
        new_lines.append(line)

with open('app/api/v1/api.py', 'w') as f:
    f.writelines(new_lines)

print("Removed webhook registration")
