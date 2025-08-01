#!/usr/bin/env python3
"""
Fix the create_enhanced_xbrl_tag function to actually set values
"""

import re
import shutil
from datetime import datetime

# Backup the file
backup_name = f"app/api/v1/endpoints/esrs_e1_full.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy("app/api/v1/endpoints/esrs_e1_full.py", backup_name)
print(f"✅ Created backup: {backup_name}")

# Read the file
with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
    content = f.read()

# Count how many times the function is defined
func_count = len(re.findall(r'def create_enhanced_xbrl_tag\(', content))
print(f"Found {func_count} definitions of create_enhanced_xbrl_tag")

# Remove all existing definitions
content = re.sub(
    r'def create_enhanced_xbrl_tag\([^)]*\):[^}]+?(?=\ndef|\nclass|\n[A-Z]|\Z)',
    '',
    content,
    flags=re.DOTALL
)

# Find a good place to insert the fixed function (after other function definitions)
insert_pos = content.find("def generate_world_class_esrs_e1_ixbrl")
if insert_pos == -1:
    insert_pos = content.rfind("\ndef ")
    
if insert_pos > 0:
    # Go back to start of line
    insert_pos = content.rfind("\n", 0, insert_pos)

# Insert the properly working function
fixed_function = '''
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
    """Create XBRL tag with all required attributes and PROPERLY SET THE VALUE"""
    
    namespace = '{http://www.xbrl.org/2013/inlineXBRL}'
    
    # Create the element with proper namespace
    if tag_type == 'nonFraction' or tag_type == 'numeric':
        tag = ET.SubElement(parent, f'{namespace}nonFraction', {
            'name': name,
            'contextRef': context_ref
        })
        
        # Add unit reference for numeric values
        if unit_ref:
            tag.set('unitRef', unit_ref)
        
        # Add decimals (default to 0)
        tag.set('decimals', str(decimals) if decimals is not None else '0')
        
        # Add scale if provided
        if scale:
            tag.set('scale', str(scale))
        
        # Add format if provided
        if format:
            tag.set('format', format)
        
        # FORMAT AND SET THE NUMERIC VALUE
        try:
            num_value = float(value) if value is not None else 0.0
            
            # Apply scale if present
            if scale:
                scale_factor = 10 ** int(scale)
                display_value = num_value / scale_factor
            else:
                display_value = num_value
            
            # Format based on decimals
            if decimals == '0' or decimals is None:
                tag.text = f"{display_value:,.0f}"
            else:
                tag.text = f"{display_value:,.{int(decimals)}f}"
                
        except (ValueError, TypeError):
            # Fallback for non-numeric values
            tag.text = str(value) if value is not None else "0"
    
    elif tag_type == 'nonNumeric' or tag_type == 'text':
        tag = ET.SubElement(parent, f'{namespace}nonNumeric', {
            'name': name,
            'contextRef': context_ref
        })
        
        # Add language
        if xml_lang:
            tag.set('{http://www.w3.org/XML/1998/namespace}lang', xml_lang)
        else:
            tag.set('{http://www.w3.org/XML/1998/namespace}lang', 'en')
        
        # SET THE TEXT VALUE WITH PROPER ESCAPING
        if value is not None:
            text_value = str(value)
            # XML escape special characters
            text_value = text_value.replace("&", "&amp;")
            text_value = text_value.replace("<", "&lt;")
            text_value = text_value.replace(">", "&gt;")
            text_value = text_value.replace('"', "&quot;")
            text_value = text_value.replace("'", "&apos;")
            tag.text = text_value
        else:
            tag.text = ""
    
    else:
        # Fallback for unknown tag types
        tag = ET.SubElement(parent, tag_type)
        tag.text = str(value) if value is not None else ""
    
    # Apply any additional attributes from kwargs
    for key, val in kwargs.items():
        if val is not None and key not in ['value']:  # Don't set 'value' as attribute
            tag.set(key, str(val))
    
    return tag
'''

# Insert the function
content = content[:insert_pos] + fixed_function + "\n" + content[insert_pos:]

# Save the fixed file
with open("app/api/v1/endpoints/esrs_e1_full.py", "w") as f:
    f.write(content)

print("✅ Fixed create_enhanced_xbrl_tag function!")
print("\nThe function now:")
print("1. Creates proper ix:nonFraction and ix:nonNumeric elements")
print("2. SETS THE TEXT VALUE (this was missing!)")
print("3. Formats numeric values with thousand separators")
print("4. Properly escapes text values")
print("5. Only has ONE definition (removed duplicates)")