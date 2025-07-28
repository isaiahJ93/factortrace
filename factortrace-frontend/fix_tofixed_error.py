import re

with open('src/app/emissions/new/page.tsx', 'r') as f:
    content = f.read()

# Find and fix any .toFixed calls that might fail
# Replace unsafe toFixed calls with safe ones
content = re.sub(
    r'(\w+)\.value\.toFixed\((\d+)\)',
    r'(\1?.value || 0).toFixed(\2)',
    content
)

# Also fix any result.value.toFixed specifically
content = re.sub(
    r'result\.value\.toFixed\((\d+)\)',
    r'(result?.value || 0).toFixed(\1)',
    content
)

# Fix any {result.value.toFixed(3)} in JSX
content = re.sub(
    r'\{result\.value\.toFixed\((\d+)\)\}',
    r'{(result?.value || 0).toFixed(\1)}',
    content
)

with open('src/app/emissions/new/page.tsx', 'w') as f:
    f.write(content)

print("Fixed toFixed errors")
