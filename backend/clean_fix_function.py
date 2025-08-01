#!/usr/bin/env python3
"""
Clean fix - remove ALL old definitions and add ONE working version
"""

import re
import shutil
from datetime import datetime

print("🧹 CLEAN FIX: Removing all old definitions and adding ONE working version")
print("="*70)

# Backup
backup = f"app/api/v1/endpoints/esrs_e1_full.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy("app/api/v1/endpoints/esrs_e1_full.py", backup)
print(f"✅ Backup created: {backup}")

# Read the file
with open("app/api/v1/endpoints/esrs_e1_full.py", "r") as f:
    content = f.read()

# Count existing definitions
existing_count = len(re.findall(r'def create_enhanced_xbrl_tag\s*\(', content))
print(f"📊 Found {existing_count} existing definitions")

# Remove ALL create_enhanced_xbrl_tag definitions
# This regex will match from 'def create_enhanced_xbrl_tag' to the next function or class
content = re.sub(
    r'def create_enhanced_xbrl_tag\s*\([^)]*\):[^}]*?(?=(?:\ndef\s+\w+|class\s+\w+|\n[A-Z_]+\s*=|\Z))',
    '',
    content,
    flags=re.DOTALL | re.MULTILINE
)

# Verify removal
remaining = len(re.findall(r'def create_enhanced_xbrl_tag\s*\(', content))
print(f"📊 After removal: {remaining} definitions remain")

# Find a good place to insert the function
# Look for other function definitions
insert_pos = -1

# Try to find a spot before generate_world_class_esrs_e1_ixbrl
match = re.search(r'\ndef generate_world_class_esrs_e1_ixbrl', content)
if match:
    insert_pos = match.start()
    print("📍 Inserting before generate_world_class_esrs_e1_ixbrl")
else:
    # Find the last function definition
    funcs = list(re.finditer(r'\ndef\s+\w+\s*\(', content))
    if funcs:
        # Insert after the last function before any class definitions
        for func in reversed(funcs):
            # Check if there's a class after this function
            next_class = content.find('\nclass ', func.end())
            if next_class == -1 or next_class > func.end() + 1000:
                insert_pos = func.end()
                # Find the end of this function
                indent_match = re.search(r'\n(?=[^\s])', content[insert_pos:])
                if indent_match:
                    insert_pos += indent_match.start()
                break

if insert_pos == -1:
    # Last resort - add at the end
    insert_pos = len(content)
    print("📍 Adding at end of file")

# The WORKING function
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
    Create proper iXBRL tags (ix:nonFraction or ix:nonNumeric)
    
    Args:
        parent: Parent XML element
        tag_type: 'nonFraction' for numbers, 'nonNumeric' for text
        name: XBRL concept name (e.g., 'esrs:Scope1Emissions')
        context_ref: Context reference ID
        value: The actual value to display
        unit_ref: Unit reference (for numeric facts)
        decimals: Decimal precision (for numeric facts)
        xml_lang: Language code (for text facts)
        scale: Scale factor (e.g., '6' for millions)
        format: iXBRL format string
        **kwargs: Additional attributes
    
    Returns:
        The created element
    """
    
    # CRITICAL: Use the full namespace URI
    IX_NS = "{http://www.xbrl.org/2013/inlineXBRL}"
    XML_NS = "{http://www.w3.org/XML/1998/namespace}"
    
    if tag_type in ['nonFraction', 'numeric']:
        # Create numeric fact element
        elem = ET.SubElement(parent, f'{IX_NS}nonFraction')
        elem.set('name', name)
        elem.set('contextRef', context_ref)
        
        # Add unit reference if provided
        if unit_ref:
            elem.set('unitRef', unit_ref)
        
        # Set decimals (default to 0 for whole numbers)
        elem.set('decimals', str(decimals) if decimals is not None else '0')
        
        # Add scale if provided
        if scale:
            elem.set('scale', str(scale))
        
        # Add format if provided
        if format:
            elem.set('format', format)
        
        # CRITICAL: FORMAT AND SET THE VALUE
        try:
            num_value = float(value) if value is not None else 0.0
            
            # Apply scale if present
            if scale:
                display_value = num_value / (10 ** int(scale))
            else:
                display_value = num_value
            
            # Format based on decimals
            if decimals == '0' or decimals is None:
                elem.text = f"{display_value:,.0f}"
            else:
                dec_places = int(decimals)
                elem.text = f"{display_value:,.{dec_places}f}"
                
        except (ValueError, TypeError):
            # Fallback for non-numeric values
            elem.text = str(value) if value is not None else "0"
    
    elif tag_type in ['nonNumeric', 'text']:
        # Create text fact element
        elem = ET.SubElement(parent, f'{IX_NS}nonNumeric')
        elem.set('name', name)
        elem.set('contextRef', context_ref)
        
        # Add language attribute
        if xml_lang:
            elem.set(f'{XML_NS}lang', xml_lang)
        else:
            elem.set(f'{XML_NS}lang', 'en')
        
        # CRITICAL: SET THE TEXT VALUE WITH PROPER ESCAPING
        if value is not None:
            text_value = str(value)
            # XML escape special characters
            text_value = text_value.replace("&", "&amp;")
            text_value = text_value.replace("<", "&lt;")
            text_value = text_value.replace(">", "&gt;")
            text_value = text_value.replace('"', "&quot;")
            text_value = text_value.replace("'", "&apos;")
            elem.text = text_value
        else:
            elem.text = ""
    
    else:
        # Fallback for other element types (shouldn't happen)
        elem = ET.SubElement(parent, tag_type)
        elem.text = str(value) if value is not None else ""
        print(f"⚠️  Warning: Unknown tag_type '{tag_type}' - expected 'nonFraction' or 'nonNumeric'")
    
    # Apply any additional attributes from kwargs
    for key, val in kwargs.items():
        if val is not None and key not in ['value', 'parent', 'tag_type', 'name', 'context_ref']:
            elem.set(key, str(val))
    
    return elem

'''

# Insert the function
content = content[:insert_pos] + working_function + content[insert_pos:]

# Save the file
with open("app/api/v1/endpoints/esrs_e1_full.py", "w") as f:
    f.write(content)

# Verify the fix
final_count = len(re.findall(r'def create_enhanced_xbrl_tag\s*\(', content))
has_ix_ns = 'IX_NS = "{http://www.xbrl.org/2013/inlineXBRL}"' in content
sets_text = 'elem.text = ' in content

print(f"\n✅ Fix complete!")
print(f"📊 Final verification:")
print(f"   Function definitions: {final_count} (should be 1)")
print(f"   Has IX_NS constant: {has_ix_ns}")
print(f"   Sets elem.text: {sets_text}")
print(f"   Function is called: {content.count('create_enhanced_xbrl_tag(')} times")

if final_count == 1 and has_ix_ns and sets_text:
    print("\n✅ SUCCESS! Function properly implemented!")
else:
    print("\n⚠️  Something might still be wrong - check manually")