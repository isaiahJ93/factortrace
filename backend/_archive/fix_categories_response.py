import re

with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    content = f.read()

# Find and fix the get_categories function
old_return = '''return {
        "1": ["stationary_combustion", "mobile_combustion", "process_emissions", "refrigerants"],
        "2": ["electricity", "heating_cooling", "steam"],
        "3": ['''

# Make sure it returns the right structure
if old_return in content:
    print("Categories endpoint looks correct")
else:
    print("Categories endpoint might be returning wrong data")

# Let's check what's actually being returned
print("\nLooking for return statement in get_categories...")
import re
pattern = r'@router.get\("/categories"\).*?return\s+({[^}]+}|.+?)(?=\n@|$)'
match = re.search(pattern, content, re.DOTALL)
if match:
    print("Found return:", match.group(1)[:200])

