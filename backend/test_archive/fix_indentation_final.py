with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Fix the generate_esrs_e1_xbrl function starting around line 1073
# The structure should be:
# 4 spaces: try:
# 8 spaces: if statements and main code
# 12 spaces: code inside if statements

for i in range(1073, 1110):
    if i >= len(lines):
        break
    
    line = lines[i]
    stripped = line.strip()
    
    if not stripped:  # Empty line
        continue
    
    # Determine correct indentation based on content
    if i == 1073 and 'try:' in line:
        lines[i] = '    try:\n'
    elif stripped.startswith('#'):  # Comments
        lines[i] = '        ' + stripped + '\n'
    elif stripped.startswith('if ') or stripped.startswith('elif '):
        lines[i] = '        ' + stripped + '\n'
    elif i > 1073 and 'data[' in stripped and '=' in stripped:
        # Assignment inside if - needs 12 spaces
        lines[i] = '            ' + stripped + '\n'
    elif stripped.startswith('validation_results'):
        lines[i] = '        ' + stripped + '\n'
    elif stripped.startswith('raise'):
        # Could be 12 or 16 spaces depending on context
        if i > 1080 and i < 1090:
            lines[i] = '                ' + stripped + '\n'
        else:
            lines[i] = '            ' + stripped + '\n'
    elif stripped.startswith('xbrl_content') or stripped.startswith('filename') or stripped.startswith('response') or stripped.startswith('background_tasks') or stripped.startswith('return'):
        lines[i] = '        ' + stripped + '\n'
    elif stripped.startswith('"') or stripped.startswith("'"):
        # String continuation
        lines[i] = '                    ' + stripped + '\n'
    elif stripped == '}' or stripped == ')':
        lines[i] = '                ' + stripped + '\n'

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed indentation for generate_esrs_e1_xbrl function")
