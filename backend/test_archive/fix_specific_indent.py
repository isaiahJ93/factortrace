with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Fix line 1003 (0-indexed: 1002)
for i, line in enumerate(lines):
    if 'categories_reported = sum(1 for v in scope3_breakdown.values()' in line:
        # Add proper 8 spaces indentation
        lines[i] = '        ' + line.lstrip()
        print(f"Fixed line {i+1}")
        break

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed categories_reported indentation")
