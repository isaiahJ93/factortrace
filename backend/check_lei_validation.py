#!/usr/bin/env python3
"""
Check why LEI validation is failing
"""

import re

print("🔍 Checking LEI validation in esrs_e1_full.py")
print("="*50)

# Read the file
with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
    content = f.read()

# Find LEI validation code
print("\n📋 Looking for LEI validation...")

# Search for LEI validation patterns
lei_patterns = [
    r'["\']lei["\'].*?["\']ABCDEFGHIJ1234567890["\']',  # Our test LEI
    r'validate.*lei',
    r'lei.*validation',
    r'Valid LEI required',
    r'lei.*required',
    r'check.*lei',
    r'lei.*pattern',
    r'lei.*regex',
    r'[A-Z0-9]{20}',  # LEI pattern
    r'esap.*submission',
]

found_matches = []
for pattern in lei_patterns:
    matches = list(re.finditer(pattern, content, re.IGNORECASE))
    if matches:
        print(f"\n🔍 Found {len(matches)} matches for pattern: {pattern}")
        for match in matches[:3]:  # Show first 3
            # Get surrounding context
            start = max(0, match.start() - 100)
            end = min(len(content), match.end() + 100)
            context = content[start:end]
            # Get line number
            line_num = content[:match.start()].count('\n') + 1
            print(f"   Line {line_num}: ...{context}...")

# Look specifically for the error message
error_msg = "Valid LEI required for ESAP submission"
error_matches = list(re.finditer(error_msg, content))
if error_matches:
    print(f"\n❌ Found error message '{error_msg}' at {len(error_matches)} location(s)")
    for match in error_matches:
        # Get the surrounding function/context
        line_num = content[:match.start()].count('\n') + 1
        print(f"   Line {line_num}")
        
        # Find the condition that triggers this
        # Look backwards for if/validation
        start = max(0, match.start() - 500)
        before_text = content[start:match.start()]
        
        # Find the condition
        if_match = re.search(r'if\s+([^:]+):', before_text[::-1])
        if if_match:
            condition = if_match.group(1)[::-1]
            print(f"   Condition: {condition}")

# Look for where LEI is checked
print("\n📍 Looking for LEI checks...")
lei_checks = re.findall(r'(.*lei.*(?:==|!=|is|not|None|False|True|len).*)', content, re.IGNORECASE)
for check in lei_checks[:10]:
    if 'def ' not in check and 'import' not in check:
        print(f"   {check.strip()}")

# Check what our test data structure looks like
print("\n🔍 Checking for expected data structure...")
entity_patterns = [
    r'data\.get\(["\']entity["\']',
    r'entity.*\.get\(["\']lei["\']',
    r'["\']lei["\'].*:.*data',
]

for pattern in entity_patterns:
    if re.search(pattern, content):
        print(f"   Found: {pattern}")

print("\n💡 Possible issues:")
print("1. LEI might need to be in a specific field (not 'lei')")
print("2. LEI validation might use a specific pattern/format")
print("3. There might be additional requirements beyond just having an LEI")
print("4. The validation might be checking a different data structure")