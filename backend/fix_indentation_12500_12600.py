#!/bin/bash

# Quick fix for the immediate error at line 12605
echo "🚑 Emergency fix for line 12605..."

# Show the problematic area
echo "Current state around line 12605:"
nl -ba app/api/v1/endpoints/esrs_e1_full.py | sed -n '12600,12610p'

# Fix the specific line
sed -i '' '12605s/^[[:space:]]*/    /' app/api/v1/endpoints/esrs_e1_full.py

echo -e "\n✅ Fixed line 12605 to have exactly 4 spaces"

# Check if there are more errors
python3 -m py_compile app/api/v1/endpoints/esrs_e1_full.py 2>&1 | head -5

echo -e "\n📋 Next steps:"
echo "1. If you see another IndentationError, run: python3 fix_indentation_12500_12600.py"
echo "2. Or use the comprehensive fix script I provided"
echo "3. The file likely has systematic indentation issues throughout"