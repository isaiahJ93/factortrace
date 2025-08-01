#!/usr/bin/env python3
"""
Diagnose what's wrong with create_enhanced_xbrl_tag
"""

import re

print("🔍 Diagnosing create_enhanced_xbrl_tag function...")
print("="*60)

# Read the file
with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
    content = f.read()

# Find all function definitions
func_defs = re.findall(r'def create_enhanced_xbrl_tag\([^)]*\):', content)
print(f"\n📊 Found {len(func_defs)} definitions of create_enhanced_xbrl_tag")

# Extract the function(s)
func_pattern = r'def create_enhanced_xbrl_tag\([^)]*\):[^}]+?(?=\ndef|\nclass|\n[A-Z]|\Z)'
matches = list(re.finditer(func_pattern, content, re.DOTALL))

for i, match in enumerate(matches):
    print(f"\n🔍 Function definition #{i+1}:")
    print("-"*60)
    
    func_text = match.group(0)
    
    # Check key aspects
    checks = {
        "Uses {namespace}nonFraction": "{namespace}nonFraction" in func_text,
        "Uses {namespace}nonNumeric": "{namespace}nonNumeric" in func_text,
        "Sets tag.text": "tag.text" in func_text or "elem.text" in func_text,
        "Has ET.SubElement": "ET.SubElement" in func_text,
        "Has proper namespace URL": "http://www.xbrl.org/2013/inlineXBRL" in func_text,
        "Sets contextRef": "contextRef" in func_text,
        "Sets unitRef": "unitRef" in func_text,
        "Handles numeric formatting": ":," in func_text or "format" in func_text
    }
    
    for check_name, found in checks.items():
        print(f"  {check_name}: {'✅' if found else '❌'}")
    
    # Look for the critical line that sets the value
    if "tag.text" in func_text:
        text_lines = [line.strip() for line in func_text.split('\n') if 'tag.text' in line]
        print(f"\n  📝 Lines that set tag.text:")
        for line in text_lines[:3]:
            print(f"     {line}")
    else:
        print("\n  ❌ NO LINES SET tag.text - THIS IS THE PROBLEM!")
    
    # Show how elements are created
    subelement_lines = [line.strip() for line in func_text.split('\n') if 'SubElement' in line]
    if subelement_lines:
        print(f"\n  🏗️ How elements are created:")
        for line in subelement_lines[:3]:
            print(f"     {line}")

print("\n"+"="*60)
print("📋 DIAGNOSIS SUMMARY:")

if len(matches) > 1:
    print("❌ PROBLEM: Multiple definitions of the same function!")
    print("   FIX: Remove duplicate definitions")
elif len(matches) == 0:
    print("❌ PROBLEM: Function not found!")
    print("   FIX: Add the function to the file")
else:
    # Single function - check if it's correct
    func_text = matches[0].group(0)
    
    has_proper_elements = "{namespace}nonFraction" in func_text or "f'{namespace}nonFraction'" in func_text
    sets_text = "tag.text" in func_text or "elem.text" in func_text
    
    if not has_proper_elements:
        print("❌ PROBLEM: Function doesn't create ix:nonFraction/ix:nonNumeric elements!")
        print("   Currently creating:", end=" ")
        if "SubElement" in func_text:
            # Find what it's creating
            elem_match = re.search(r"SubElement\s*\([^,]+,\s*['\"]([^'\"]+)['\"]", func_text)
            if elem_match:
                print(elem_match.group(1))
        print("   FIX: Use f'{namespace}nonFraction' or f'{namespace}nonNumeric'")
    
    if not sets_text:
        print("❌ PROBLEM: Function doesn't set the element's text value!")
        print("   FIX: Add tag.text = <formatted_value> after creating element")
    
    if has_proper_elements and sets_text:
        print("✅ Function looks correct!")
        print("   If still not working, check:")
        print("   1. Is the function being called?")
        print("   2. Are the parameters correct?")
        print("   3. Is the output being used?")

# Show usage in the file
print("\n🔍 Function usage:")
usage_count = len(re.findall(r'create_enhanced_xbrl_tag\s*\(', content))
print(f"   Function is called {usage_count} times")

if usage_count > 0:
    # Show a few examples
    usage_examples = re.findall(r'create_enhanced_xbrl_tag\s*\([^)]+\)', content)[:3]
    print("\n   Example calls:")
    for ex in usage_examples:
        # Clean up for display
        ex_clean = ' '.join(ex.split())[:100] + "..." if len(ex) > 100 else ex
        print(f"   - {ex_clean}")