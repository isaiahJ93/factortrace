#!/usr/bin/env python3
"""
Force fix - completely rewrite the problematic parts
"""

import re
import shutil
from datetime import datetime

print("🔨 FORCE FIX: Complete rewrite of create_enhanced_xbrl_tag")
print("="*60)

# Backup
backup = f"app/api/v1/endpoints/esrs_e1_full.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy("app/api/v1/endpoints/esrs_e1_full.py", backup)
print(f"✅ Backup: {backup}")

# Read file
with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
    content = f.read()

# Count and show current definitions
current_defs = re.findall(r'(def create_enhanced_xbrl_tag\s*\([^)]*\):[^\n]*)', content)
print(f"\n📊 Found {len(current_defs)} definitions:")
for i, defn in enumerate(current_defs):
    print(f"   {i+1}. {defn[:80]}...")

# AGGRESSIVE REMOVAL - remove everything between def and the next def/class
print("\n🗑️  Removing ALL create_enhanced_xbrl_tag definitions...")

# Pattern to match the entire function including its body
pattern = r'def create_enhanced_xbrl_tag\s*\([^)]*\):[^}]*?(?=(?:^def\s|\nclass\s|^class\s|\Z))'

# Remove all matches
content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)

# Double check - use line-by-line removal
lines = content.split('\n')
new_lines = []
skip_lines = False
indent_level = 0

for line in lines:
    # Check if this starts a create_enhanced_xbrl_tag definition
    if 'def create_enhanced_xbrl_tag' in line:
        skip_lines = True
        # Get the indentation level
        indent_level = len(line) - len(line.lstrip())
        continue
    
    # If we're skipping, check if we've reached the end of the function
    if skip_lines:
        # Check if this line is at the same or lower indentation level (and not empty)
        if line.strip() and (len(line) - len(line.lstrip()) <= indent_level):
            # This is a new function/class/statement at the same level
            skip_lines = False
        else:
            # Still inside the function, skip this line
            continue
    
    # Keep this line
    new_lines.append(line)

content = '\n'.join(new_lines)

# Verify removal
remaining = len(re.findall(r'def create_enhanced_xbrl_tag\s*\(', content))
print(f"📊 After removal: {remaining} definitions remain")

# Find where to insert - right before generate_world_class_esrs_e1_ixbrl
insert_match = re.search(r'(\n)(def generate_world_class_esrs_e1_ixbrl)', content)
if insert_match:
    insert_pos = insert_match.start(1)
else:
    # Alternative: find a good spot
    insert_match = re.search(r'(\n\n)(def \w+.*?generate.*?ixbrl)', content, re.IGNORECASE)
    if insert_match:
        insert_pos = insert_match.start(1)
    else:
        # Last resort: before the last major function
        insert_pos = content.rfind('\n\ndef ') 

# The CORRECT working function
working_function = '''

def create_enhanced_xbrl_tag(
    parent: ET.Element,
    tag_type: str,
    name: str,
    context_ref: str,
    value: Any,
    unit_ref: str = None,
    decimals: str = None,
    xml_lang: str = None,
    scale: str = None,
    format: str = None,
    **kwargs
) -> ET.Element:
    """
    Create proper iXBRL tags - WORKING VERSION
    
    This function MUST:
    1. Create elements with full namespace URI
    2. Set all required attributes
    3. SET THE TEXT VALUE (critical!)
    """
    
    # Full namespace URIs - DO NOT CHANGE
    IX_NS = "{http://www.xbrl.org/2013/inlineXBRL}"
    XML_NS = "{http://www.w3.org/XML/1998/namespace}"
    
    if tag_type in ['nonFraction', 'numeric']:
        # Create ix:nonFraction element with full namespace
        elem = ET.SubElement(parent, IX_NS + 'nonFraction')
        
        # Required attributes
        elem.set('name', name)
        elem.set('contextRef', context_ref)
        
        # Optional attributes
        if unit_ref:
            elem.set('unitRef', unit_ref)
        
        elem.set('decimals', str(decimals) if decimals is not None else '0')
        
        if scale:
            elem.set('scale', str(scale))
        
        if format:
            elem.set('format', format)
        
        # CRITICAL: SET THE TEXT VALUE
        if value is not None:
            try:
                num_value = float(value)
                
                # Apply scale if present
                if scale:
                    display_value = num_value / (10 ** int(scale))
                else:
                    display_value = num_value
                
                # Format based on decimals
                if decimals == '0' or decimals is None:
                    elem.text = "{:,.0f}".format(display_value)
                else:
                    elem.text = "{:,.{}f}".format(display_value, int(decimals))
            except (ValueError, TypeError):
                elem.text = str(value)
        else:
            elem.text = "0"
    
    elif tag_type in ['nonNumeric', 'text']:
        # Create ix:nonNumeric element with full namespace
        elem = ET.SubElement(parent, IX_NS + 'nonNumeric')
        
        # Required attributes
        elem.set('name', name)
        elem.set('contextRef', context_ref)
        
        # Language attribute
        if xml_lang:
            elem.set(XML_NS + 'lang', xml_lang)
        else:
            elem.set(XML_NS + 'lang', 'en')
        
        # CRITICAL: SET THE TEXT VALUE WITH ESCAPING
        if value is not None:
            text_value = str(value)
            # XML escape
            text_value = text_value.replace("&", "&amp;")
            text_value = text_value.replace("<", "&lt;")
            text_value = text_value.replace(">", "&gt;")
            text_value = text_value.replace('"', "&quot;")
            text_value = text_value.replace("'", "&apos;")
            elem.text = text_value
        else:
            elem.text = ""
    
    else:
        # Unknown tag type - log warning
        print(f"WARNING: Unknown tag_type '{tag_type}' in create_enhanced_xbrl_tag")
        elem = ET.SubElement(parent, tag_type)
        elem.text = str(value) if value is not None else ""
    
    # Apply any extra attributes
    for key, val in kwargs.items():
        if val is not None and key not in ['value']:
            elem.set(key, str(val))
    
    return elem

'''

# Insert the function
content = content[:insert_pos] + working_function + content[insert_pos:]

# Add namespace registrations if missing
if "ET.register_namespace('ix'" not in content:
    # Find imports section
    import_section = re.search(r'(import.*?\n)(\n|from|def|class)', content, re.DOTALL)
    if import_section:
        insert_pos = import_section.end(1)
        namespace_registration = '''
# Register namespaces for iXBRL
ET.register_namespace('', 'http://www.w3.org/1999/xhtml')
ET.register_namespace('ix', 'http://www.xbrl.org/2013/inlineXBRL')
ET.register_namespace('xbrli', 'http://www.xbrl.org/2003/instance')
ET.register_namespace('xbrldi', 'http://xbrl.org/2006/xbrldi')
ET.register_namespace('iso4217', 'http://www.xbrl.org/2003/iso4217')
ET.register_namespace('esrs', 'http://www.efrag.org/esrs/2023')

'''
        content = content[:insert_pos] + namespace_registration + content[insert_pos:]
        print("✅ Added namespace registrations")

# Save the file
with open("app/api/v1/endpoints/esrs_e1_full.py", "w") as f:
    f.write(content)

# Final verification
final_count = len(re.findall(r'def create_enhanced_xbrl_tag\s*\(', content))
has_registrations = "ET.register_namespace('ix'" in content
correct_implementation = 'IX_NS + \'nonFraction\'' in content or 'IX_NS + "nonFraction"' in content

print(f"\n✅ FORCE FIX COMPLETE!")
print(f"📊 Final verification:")
print(f"   Function definitions: {final_count} {'✅' if final_count == 1 else '❌'}")
print(f"   Namespace registrations: {'✅' if has_registrations else '❌'}")
print(f"   Correct implementation: {'✅' if correct_implementation else '❌'}")
print(f"   Function calls: {content.count('create_enhanced_xbrl_tag(')}")

if final_count != 1:
    print("\n⚠️  Still have multiple definitions! Running line-by-line check...")
    # Show where they are
    for match in re.finditer(r'def create_enhanced_xbrl_tag\s*\(', content):
        line_num = content[:match.start()].count('\n') + 1
        print(f"   Found at line {line_num}")