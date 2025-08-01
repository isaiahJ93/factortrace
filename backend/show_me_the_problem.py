#!/usr/bin/env python3
"""
Show exactly what's wrong with iXBRL generation
"""

import re

print("🔍 DIAGNOSING YOUR iXBRL PROBLEM")
print("="*50)

# Read the file
with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
    content = f.read()

# 1. Count function definitions
func_count = len(re.findall(r'def create_enhanced_xbrl_tag\s*\(', content))
print(f"\n1️⃣ Function definitions: {func_count}")
if func_count == 0:
    print("   ❌ NO FUNCTION FOUND!")
elif func_count == 1:
    print("   ✅ Single definition (good)")
else:
    print(f"   ❌ MULTIPLE DEFINITIONS ({func_count}) - This is a problem!")

# 2. Check if it creates proper elements
creates_proper = bool(re.search(r'IX_NS.*nonFraction|{.*inlineXBRL.*}nonFraction', content))
print(f"\n2️⃣ Creates ix:nonFraction elements: {'✅ Yes' if creates_proper else '❌ No'}")

# 3. Check if it sets text
sets_text = bool(re.search(r'elem\.text\s*=', content))
print(f"\n3️⃣ Sets element text value: {'✅ Yes' if sets_text else '❌ No'}")

# 4. Check namespace registrations
has_ns_reg = bool(re.search(r"ET\.register_namespace\s*\(\s*'ix'", content))
print(f"\n4️⃣ Has namespace registrations: {'✅ Yes' if has_ns_reg else '❌ No'}")

# 5. Check how many times it's called
call_count = len(re.findall(r'create_enhanced_xbrl_tag\s*\(', content))
print(f"\n5️⃣ Function is called: {call_count} times")

# 6. Check a sample call
calls = re.findall(r'create_enhanced_xbrl_tag\s*\([^)]+\)', content)
if calls:
    print("\n6️⃣ Sample function call:")
    sample = calls[0]
    print(f"   {sample[:100]}...")
    
    # Check the tag type
    tag_match = re.search(r"['\"](\w+)['\"]", sample)
    if tag_match:
        tag_type = tag_match.group(1)
        print(f"   Tag type: '{tag_type}' {'✅' if tag_type in ['nonFraction', 'nonNumeric'] else '❌ WRONG!'}")

# 7. Check for validation blocking
has_lei_block = bool(re.search(r'Valid LEI required.*ESAP', content))
print(f"\n7️⃣ Has LEI validation blocking: {'❌ Yes - THIS BLOCKS GENERATION' if has_lei_block else '✅ No'}")

# Summary
print("\n" + "="*50)
print("📊 DIAGNOSIS:")

problems = []
if func_count != 1:
    problems.append(f"Wrong number of function definitions ({func_count})")
if not creates_proper:
    problems.append("Function doesn't create proper ix: elements")
if not sets_text:
    problems.append("Function doesn't set element text")
if not has_ns_reg:
    problems.append("Missing namespace registrations")
if has_lei_block:
    problems.append("LEI validation blocks even valid LEIs")

if problems:
    print("\n❌ PROBLEMS FOUND:")
    for p in problems:
        print(f"   - {p}")
    
    print("\n🔧 TO FIX:")
    print("   1. Run: python3 force_fix_now.py")
    print("   2. Run: python3 manual_ixbrl_test.py (to verify iXBRL works)")
    print("   3. Restart your FastAPI server")
else:
    print("\n✅ Code looks correct!")
    print("   If still not working, check:")
    print("   - Is the function being called?")
    print("   - Are there runtime errors?")
    print("   - Is validation blocking?")

# Quick test
print("\n8️⃣ Quick test files:")
import os
test_files = ['manual_ixbrl.xhtml', 'minimal_test.xhtml', 'direct_test.xhtml']
for f in test_files:
    if os.path.exists(f):
        with open(f, 'r') as file:
            content = file.read()
            if '<ix:nonFraction' in content:
                print(f"   ✅ {f} - HAS iXBRL tags")
            else:
                print(f"   ❌ {f} - NO iXBRL tags")