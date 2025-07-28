import re

with open('src/app/emissions/new/page.tsx', 'r') as f:
    content = f.read()

# Add debug log after factorsByCategory
debug_code = '''  const factorsByCategory = factors.reduce((acc, factor) => {
    const category = factor.category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(factor);
    return acc;
  }, {} as Record<string, any[]>);
  
  // DEBUG
  console.log('Factors:', factors);
  console.log('FactorsByCategory:', factorsByCategory);
  console.log('Selected Category:', selectedCategory);'''

# Replace the existing factorsByCategory code
pattern = r'const factorsByCategory = factors\.reduce.*?\}, \{\} as Record<string, any\[\]\>\);'
content = re.sub(pattern, debug_code, content, flags=re.DOTALL)

with open('src/app/emissions/new/page.tsx', 'w') as f:
    f.write(content)

print("Added debug logging")
