#!/usr/bin/env python3
import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find the validate_boundary_changes function and check its structure
# Let's look for the problematic line
pattern = r'if not change\.get\(\'emissions_impact\'\):'
match = re.search(pattern, content)

if match:
    # Get context around this line
    start = max(0, match.start() - 500)
    end = min(len(content), match.end() + 500)
    context = content[start:end]
    
    print("Found problematic code context:")
    print("-" * 50)
    print(context)
    print("-" * 50)
    
    # The issue is that 'change' is expected to be a dict but it's a string
    # Let's fix the iteration to handle the actual data structure
    # Replace the problematic section
    content = re.sub(
        r'for change in changes:\s*if not change\.get\(\'emissions_impact\'\):',
        '''for change in changes:
        if isinstance(change, str):
            # Handle string format
            validation['warnings'].append(f'Boundary change not properly structured: {change}')
            continue
        if isinstance(change, dict) and not change.get('emissions_impact'):''',
        content
    )
    
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Fixed boundary validation to handle different data formats")
else:
    print("❌ Could not find the problematic line")

# Let's also check what format the function expects
print("\nLooking for the expected boundary_changes format...")
boundary_func = re.search(r'def validate_boundary_changes\(data\):(.*?)(?=\ndef|\Z)', content, re.DOTALL)
if boundary_func:
    func_content = boundary_func.group(0)
    # Extract what it expects
    if 'boundary_changes' in func_content:
        print("The function expects boundary_changes in the data")
