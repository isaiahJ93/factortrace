with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    content = f.read()

# Replace the incorrectly indented line
content = content.replace('        mock_factors = [', '    mock_factors = [')

# Also check for any other lines with 8 spaces that should have 4
lines = content.split('\n')
fixed_lines = []
inside_function = False

for i, line in enumerate(lines):
    # If we see a function definition, we're inside a function
    if line.strip().startswith('def ') and line.strip().endswith(':'):
        inside_function = True
    elif line.strip() and not line.startswith(' ') and not line.startswith('\t'):
        inside_function = False
    
    # Fix lines that have 8 spaces at the start when they should have 4
    if inside_function and line.startswith('        ') and not line.startswith('            '):
        # This line has 8 spaces, should probably be 4
        if i > 0 and lines[i-1].strip().endswith(':'):
            # Previous line ends with colon, so this should be indented by 4
            fixed_lines.append('    ' + line[8:])
            print(f"Fixed line {i+1}: {line[:30]}...")
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Write back
with open('app/api/v1/endpoints/emission_factors.py', 'w') as f:
    f.write('\n'.join(fixed_lines))

print("Fixed indentation issues")
