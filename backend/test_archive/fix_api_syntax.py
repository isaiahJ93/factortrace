# Read the file
with open('app/api/v1/api.py', 'r') as f:
    lines = f.readlines()

# Find and fix the syntax error around line 414
for i in range(len(lines)):
    if i >= 410 and i <= 420:
        print(f"Line {i+1}: {lines[i].rstrip()}")

# Remove the problematic line for now
if 'api_router.include_router(verify_voucher.router, prefix="/verify", tags=["voucher"])' in ''.join(lines):
    lines = [line for line in lines if 'verify_voucher.router' not in line]

# Write back
with open('app/api/v1/api.py', 'w') as f:
    f.writelines(lines)

print("\n✅ Removed problematic line. Let's add it properly.")
