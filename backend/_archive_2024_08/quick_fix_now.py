#!/usr/bin/env python3
"""
Quick fix to ensure create_enhanced_xbrl_tag works NOW
"""

import shutil
from datetime import datetime

print("🚀 QUICK FIX: Ensuring create_enhanced_xbrl_tag creates proper iXBRL")
print("="*60)

# Backup
backup = f"app/api/v1/endpoints/esrs_e1_full.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy("app/api/v1/endpoints/esrs_e1_full.py", backup)
print(f"✅ Backup created: {backup}")

# Read file
with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
    lines = f.readlines()

# Find and replace the function
in_function = False
function_start = -1
indent_level = 0
new_lines = []

i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this is the start of create_enhanced_xbrl_tag
    if line.strip().startswith("def create_enhanced_xbrl_tag("):
        print(f"Found function definition at line {i+1}")
        in_function = True
        function_start = i
        indent_level = len(line) - len(line.lstrip())
        
        # Skip to the end of this function
        j = i + 1
        while j < len(lines):
            next_line = lines[j]
            if next_line.strip() and not next_line.startswith(' ') and not next_line.startswith('\t'):
                # Found next top-level item
                break
            if next_line.strip().startswith("def ") and len(next_line) - len(next_line.lstrip()) <= indent_level:
                # Found next function at same or lower indent
                break
            j += 1
        
        # Insert our working function
        new_lines.append('''def create_enhanced_xbrl_tag(
    parent: ET.Element,
    tag_type: str,
    name: str,
    context_ref: str,
    value: Any,
    unit_ref: str = None,
    decimals: str = None,
    xml_lang: str = None,
    **kwargs
) -> ET.Element:
    """Create proper iXBRL tags that ACTUALLY WORK"""
    
    # CRITICAL: Full namespace URI
    IX_NS = "{http://www.xbrl.org/2013/inlineXBRL}"
    
    if tag_type in ['nonFraction', 'numeric']:
        # Create ix:nonFraction element
        elem = ET.SubElement(parent, f'{IX_NS}nonFraction')
        elem.set('name', name)
        elem.set('contextRef', context_ref)
        
        if unit_ref:
            elem.set('unitRef', unit_ref)
        
        elem.set('decimals', str(decimals) if decimals is not None else '0')
        
        # FORMAT AND SET THE VALUE - THIS IS CRITICAL!
        try:
            num_val = float(value) if value is not None else 0
            if decimals == '0' or decimals is None:
                elem.text = f"{num_val:,.0f}"
            else:
                elem.text = f"{num_val:,.{int(decimals)}f}"
        except:
            elem.text = str(value)
    
    elif tag_type in ['nonNumeric', 'text']:
        # Create ix:nonNumeric element
        elem = ET.SubElement(parent, f'{IX_NS}nonNumeric')
        elem.set('name', name)
        elem.set('contextRef', context_ref)
        
        if xml_lang:
            elem.set('{http://www.w3.org/XML/1998/namespace}lang', xml_lang)
        else:
            elem.set('{http://www.w3.org/XML/1998/namespace}lang', 'en')
        
        # SET THE TEXT VALUE - THIS IS CRITICAL!
        if value is not None:
            text = str(value)
            # XML escape
            text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            text = text.replace('"', "&quot;").replace("'", "&apos;")
            elem.text = text
        else:
            elem.text = ""
    
    else:
        # Fallback
        elem = ET.SubElement(parent, tag_type)
        elem.text = str(value) if value is not None else ""
    
    # Apply any extra attributes
    for k, v in kwargs.items():
        if v is not None and k != 'value':
            elem.set(k, str(v))
    
    return elem

''')
        # Skip the old function
        i = j
        continue
    
    # Not in the function, keep the line
    if not in_function:
        new_lines.append(line)
    
    i += 1

# Write the fixed file
with open("app/api/v1/endpoints/esrs_e1_full.py", "w") as f:
    f.writelines(new_lines)

print("✅ Function replaced with working version!")

# Verify the fix
with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
    content = f.read()

# Count functions
import re
func_count = len(re.findall(r'def create_enhanced_xbrl_tag\(', content))
print(f"\n📊 Verification:")
print(f"   Function definitions: {func_count} (should be 1)")
print(f"   Has IX_NS constant: {'IX_NS = ' in content}")
print(f"   Creates nonFraction: {'{IX_NS}nonFraction' in content}")
print(f"   Sets elem.text: {'elem.text = ' in content}")

print("\n✅ Fix applied! Now test with:")
print("   python3 test_with_valid_lei.py")