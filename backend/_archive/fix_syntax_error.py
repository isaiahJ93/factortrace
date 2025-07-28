with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    content = f.read()

# The issue is a malformed line with "] == scope]"
# This should probably be part of a list comprehension or filter
content = content.replace('    ] == scope]', '    ]')

# Also look for the pattern that might be broken
# It seems like there's a broken list comprehension
lines = content.split('\n')
for i, line in enumerate(lines):
    if '] == scope]' in line:
        print(f"Found broken syntax on line {i+1}: {line}")
        # This looks like it should be: [x for x in mock_factors if x['scope'] == scope]
        # Let's check the context
        if i > 0:
            print(f"Previous line: {lines[i-1]}")

# Fix the specific pattern
# Look for where mock_factors is being filtered
import re
# Find and fix the broken comprehension
pattern = r'mock_factors = \[(.*?)\] == scope\]'
if re.search(pattern, content, re.DOTALL):
    print("Found broken list comprehension")
    content = re.sub(pattern, 'mock_factors = [f for f in mock_factors if f.get("scope") == scope]', content, flags=re.DOTALL)

# Write the fixed content
with open('app/api/v1/endpoints/emission_factors.py', 'w') as f:
    f.write(content)

print("Fixed syntax error")

# Show the fixed area
with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    lines = f.readlines()
    print("\nLines 195-205 after fix:")
    for i in range(195, min(205, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')

