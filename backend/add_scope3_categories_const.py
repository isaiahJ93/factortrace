import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Check if SCOPE3_CATEGORIES is defined
if 'SCOPE3_CATEGORIES = {' not in content:
    # Add it after imports
    scope3_const = '''
# Scope 3 categories mapping
SCOPE3_CATEGORIES = {
    1: "Purchased goods and services",
    2: "Capital goods",
    3: "Fuel-and-energy-related activities",
    4: "Upstream transportation and distribution",
    5: "Waste generated in operations",
    6: "Business travel",
    7: "Employee commuting",
    8: "Upstream leased assets",
    9: "Downstream transportation and distribution",
    10: "Processing of sold products",
    11: "Use of sold products",
    12: "End-of-life treatment of sold products",
    13: "Downstream leased assets",
    14: "Franchises",
    15: "Investments"
}
'''
    
    # Find a good place to insert - after imports, before first function
    import_end = content.find('\n\n\n') if '\n\n\n' in content else content.find('\n\ndef ')
    if import_end > 0:
        content = content[:import_end] + '\n' + scope3_const + content[import_end:]
    else:
        # Just add after imports
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('def ') or line.startswith('class '):
                lines.insert(i, scope3_const)
                break
        content = '\n'.join(lines)
    
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
        f.write(content)
    
    print("✅ Added SCOPE3_CATEGORIES constant")
else:
    print("SCOPE3_CATEGORIES already defined")

