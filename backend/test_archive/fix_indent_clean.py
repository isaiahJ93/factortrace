with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Fix any indentation issues by finding and fixing the problematic line
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'categories_reported = sum(1 for v in scope3_breakdown.values()' in line:
        # Count the indentation of the previous line
        if i > 0:
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
            lines[i] = ' ' * prev_indent + line.lstrip()
            print(f"Fixed line {i+1}: {lines[i][:50]}...")

content = '\n'.join(lines)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed indentation")
