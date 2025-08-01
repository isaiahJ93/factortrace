#!/usr/bin/env python3
"""
Test the current state of esrs_e1_full.py
"""

import re

print("🔍 Testing current state of esrs_e1_full.py")
print("="*50)

# Read the file
try:
    with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
        content = f.read()
except FileNotFoundError:
    print("❌ File not found!")
    exit(1)

# Check for function definitions
func_count = len(re.findall(r'def create_enhanced_xbrl_tag\s*\(', content))
print(f"\n📊 create_enhanced_xbrl_tag definitions: {func_count}")

if func_count == 0:
    print("❌ Function not found!")
elif func_count > 1:
    print("⚠️  Multiple definitions found - this will cause issues!")
else:
    print("✅ Single definition found")

# Check for key elements
checks = {
    "IX_NS constant": r'IX_NS\s*=\s*["\'].*inlineXBRL',
    "Creates nonFraction": r'{IX_NS}nonFraction|{.*inlineXBRL.*}nonFraction',
    "Creates nonNumeric": r'{IX_NS}nonNumeric|{.*inlineXBRL.*}nonNumeric', 
    "Sets elem.text": r'elem\.text\s*=',
    "Has try/except for numbers": r'try:.*float.*except',
    "Escapes XML characters": r'replace.*&amp;|replace.*&lt;',
}

print("\n🔍 Function implementation checks:")
for name, pattern in checks.items():
    found = bool(re.search(pattern, content, re.DOTALL))
    print(f"   {name}: {'✅' if found else '❌'}")

# Check how it's being called
print("\n📞 Function usage:")
calls = re.findall(r"create_enhanced_xbrl_tag\s*\([^)]+\)", content)
print(f"   Total calls: {len(calls)}")

if calls:
    # Check first few calls
    print("\n   Sample calls:")
    for i, call in enumerate(calls[:3]):
        # Extract tag_type parameter
        match = re.search(r"'(nonFraction|nonNumeric|[^']+)'", call)
        if match:
            tag_type = match.group(1)
            print(f"   {i+1}. tag_type='{tag_type}' {'✅' if tag_type in ['nonFraction', 'nonNumeric'] else '❌'}")

# Check for namespace registrations
print("\n📋 Namespace registrations:")
ns_checks = {
    "ix namespace": r"ET\.register_namespace\s*\(\s*'ix'",
    "empty namespace": r"ET\.register_namespace\s*\(\s*''",
    "xbrli namespace": r"ET\.register_namespace\s*\(\s*'xbrli'",
}

for name, pattern in ns_checks.items():
    found = bool(re.search(pattern, content))
    print(f"   {name}: {'✅' if found else '❌'}")

# Summary
print("\n" + "="*50)
print("📊 SUMMARY:")

issues = []
if func_count == 0:
    issues.append("Function not defined")
elif func_count > 1:
    issues.append("Multiple function definitions")

if not re.search(r'elem\.text\s*=', content):
    issues.append("Function doesn't set element text")

if not re.search(r'{IX_NS}nonFraction|{.*inlineXBRL.*}nonFraction', content, re.DOTALL):
    issues.append("Function doesn't create proper iXBRL elements")

if issues:
    print("❌ Issues found:")
    for issue in issues:
        print(f"   - {issue}")
    print("\n🔧 Run this to fix: python3 clean_fix_function.py")
else:
    print("✅ Function appears to be correctly implemented!")
    print("\n🧪 Test it with: python3 test_with_valid_lei.py")