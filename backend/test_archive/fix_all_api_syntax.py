#!/usr/bin/env python3
import re

# Read the file
with open('app/api/v1/api.py', 'r') as f:
    content = f.read()

# Fix pattern 1: unterminated string with ["vouc
content = re.sub(
    r'api_router\.include_router\(verify_voucher\.router, prefix="/verify", tags=\["vouc\s*\n\s*her"\]\)',
    'api_router.include_router(verify_voucher.router, prefix="/verify", tags=["voucher"])',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Fix pattern 2: standalone her"])
content = re.sub(
    r'^\s*her"\]\)\s*$',
    '',
    content,
    flags=re.MULTILINE
)

# Fix any broken include_router calls
lines = content.split('\n')
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Check if this line has an incomplete include_router
    if 'api_router.include_router' in line and not line.strip().endswith(')'):
        # Collect the full statement
        full_statement = line
        j = i + 1
        while j < len(lines) and not lines[j].strip().endswith(')'):
            full_statement += ' ' + lines[j].strip()
            j += 1
        if j < len(lines):
            full_statement += ' ' + lines[j].strip()
        
        # Fix the statement
        if 'verify_voucher' in full_statement and '["vouc' in full_statement:
            fixed_lines.append('api_router.include_router(verify_voucher.router, prefix="/verify", tags=["voucher"])')
            i = j + 1
            continue
    
    fixed_lines.append(line)
    i += 1

# Join back
content = '\n'.join(fixed_lines)

# Remove any duplicate include_router calls
lines = content.split('\n')
seen_includes = set()
final_lines = []
for line in lines:
    if 'api_router.include_router' in line:
        if line.strip() not in seen_includes:
            seen_includes.add(line.strip())
            final_lines.append(line)
    else:
        final_lines.append(line)

content = '\n'.join(final_lines)

# Save the file
with open('app/api/v1/api.py', 'w') as f:
    f.write(content)

print("✅ Fixed all syntax errors in api.py")

# Verify the file is valid Python
try:
    compile(content, 'app/api/v1/api.py', 'exec')
    print("✅ File is valid Python")
except SyntaxError as e:
    print(f"❌ Still has syntax error: {e}")
    print(f"   Line {e.lineno}: {e.text}")
