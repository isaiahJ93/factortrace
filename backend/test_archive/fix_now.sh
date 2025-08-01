#!/bin/bash

echo "🚀 FIXING iXBRL GENERATION NOW"
echo "=============================="
echo ""

# Step 1: Check current state
echo "1️⃣ Checking current state..."
python3 test_current_state.py

# Step 2: Apply clean fix
echo -e "\n2️⃣ Applying clean fix..."
python3 clean_fix_function.py

# Step 3: Test with valid data
echo -e "\n3️⃣ Testing generation..."
python3 test_with_valid_lei.py

# Step 4: Check output
echo -e "\n4️⃣ Checking for output files..."
for f in esrs*.xhtml esrs*.html; do
    if [ -f "$f" ]; then
        echo "Found: $f"
        python3 -c "
import re
with open('$f', 'r') as file:
    content = file.read()
    fractions = len(re.findall(r'<ix:nonFraction', content))
    numerics = len(re.findall(r'<ix:nonNumeric', content)) 
    print(f'  - ix:nonFraction tags: {fractions}')
    print(f'  - ix:nonNumeric tags: {numerics}')
    if fractions > 0 or numerics > 0:
        print('  ✅ Contains iXBRL tags!')
"
    fi
done

echo -e "\n✅ Fix process complete!"
echo ""
echo "If you see iXBRL tags above, it worked!"
echo "Otherwise, check the error messages."