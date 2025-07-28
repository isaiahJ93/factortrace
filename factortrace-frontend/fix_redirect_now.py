import re

# Fix the calculator page redirect
try:
    with open('src/app/calculator/page.tsx', 'r') as f:
        content = f.read()
    
    # Remove ALL redirects to dashboard
    content = re.sub(r'router\.push\([\'"]\/dashboard[\'"]\);?', '// REDIRECT REMOVED', content)
    content = re.sub(r'setTimeout\(\(\)\s*=>\s*{\s*router\.push\([\'"]\/dashboard[\'"]\);\s*},\s*\d+\);', '// AUTO-REDIRECT REMOVED', content)
    
    with open('src/app/calculator/page.tsx', 'w') as f:
        f.write(content)
    print("✅ Removed dashboard redirects from calculator page")
except:
    print("❌ Calculator page not found")

# Also check the EliteGHGCalculator component
try:
    with open('src/components/emissions/EliteGHGCalculator.tsx', 'r') as f:
        content = f.read()
    
    # Find onCalculationComplete callback
    if 'onCalculationComplete' in content and 'router.push' in content:
        content = re.sub(r'onCalculationComplete\?\..*', '// onCalculationComplete?.(data);', content)
    
    with open('src/components/emissions/EliteGHGCalculator.tsx', 'w') as f:
        f.write(content)
    print("✅ Fixed calculator component")
except:
    pass
