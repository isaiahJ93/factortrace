#!/usr/bin/env python3
"""
Patch script to add proper iXBRL tagging to esrs_e1_full.py
Run this to update your existing implementation
"""

import os
import re

def patch_esrs_e1_full():
    """Add iXBRL tagging functions to existing esrs_e1_full.py"""
    
    file_path = "app/api/v1/endpoints/esrs_e1_full.py"
    
    # Read the existing file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already patched
    if "create_ix_nonfraction" in content:
        print("✅ File already has iXBRL functions!")
        return
    
    # Find where to insert the functions (after imports)
    import_section_end = content.rfind("from") + content[content.rfind("from"):].find("\n")
    
    # iXBRL helper functions to insert
    ixbrl_functions = '''

# ==================== iXBRL Helper Functions ====================

def escape_xbrl_string(value: Any) -> str:
    """Escape string for XBRL/XML compliance"""
    if value is None:
        return ""
    text = str(value)
    # XML escape
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace('"', "&quot;").replace("'", "&apos;")
    # Remove control characters
    text = re.sub(r'[\\x00-\\x08\\x0B-\\x0C\\x0E-\\x1F\\x7F]', '', text)
    return text

def create_numeric_fact(parent: ET.Element, concept: str, value: Union[int, float], 
                       context_ref: str, unit_ref: str, decimals: str = "0") -> ET.Element:
    """Create ix:nonFraction element for numeric facts"""
    elem = ET.SubElement(parent, "{http://www.xbrl.org/2013/inlineXBRL}nonFraction", {
        "name": concept,
        "contextRef": context_ref,
        "unitRef": unit_ref,
        "decimals": decimals
    })
    elem.text = f"{value:,.0f}" if isinstance(value, int) else f"{value:,.2f}"
    return elem

def create_text_fact(parent: ET.Element, concept: str, value: str, 
                    context_ref: str) -> ET.Element:
    """Create ix:nonNumeric element for text facts"""
    elem = ET.SubElement(parent, "{http://www.xbrl.org/2013/inlineXBRL}nonNumeric", {
        "name": concept,
        "contextRef": context_ref
    })
    elem.text = escape_xbrl_string(value)
    return elem

'''
    
    # Find the generate_world_class_esrs_e1_ixbrl function
    func_match = re.search(r'def generate_world_class_esrs_e1_ixbrl\(.*?\):', content)
    if not func_match:
        print("❌ Could not find generate_world_class_esrs_e1_ixbrl function!")
        return
    
    # Insert the helper functions after imports
    content = content[:import_section_end] + ixbrl_functions + content[import_section_end:]
    
    # Now find where emissions are being added to the HTML
    # Look for patterns like "Scope 1" or scope1_total
    
    # Pattern to replace plain text/number insertion with iXBRL tags
    replacements = [
        # Replace scope 1 emissions display
        (r'(<td[^>]*>)(\s*)([\d,\.]+)(\s*)(</td>)(\s*<!--\s*scope1\s*-->)', 
         r'\1\2<ix:nonFraction name="esrs:Scope1Emissions" contextRef="current-period" unitRef="u-tCO2e" decimals="0">\3</ix:nonFraction>\4\5\6'),
        
        # Replace scope 2 location-based
        (r'(<td[^>]*>)(\s*)([\d,\.]+)(\s*)(</td>)(\s*<!--\s*scope2.*location\s*-->)',
         r'\1\2<ix:nonFraction name="esrs:Scope2LocationBased" contextRef="current-period" unitRef="u-tCO2e" decimals="0">\3</ix:nonFraction>\4\5\6'),
        
        # Replace scope 3 emissions
        (r'(<td[^>]*>)(\s*)([\d,\.]+)(\s*)(</td>)(\s*<!--\s*scope3\s*-->)',
         r'\1\2<ix:nonFraction name="esrs:Scope3Emissions" contextRef="current-period" unitRef="u-tCO2e" decimals="0">\3</ix:nonFraction>\4\5\6'),
    ]
    
    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    # Find where to properly tag emissions values
    # Look for where emission values are being inserted
    
    # Pattern to find emission value insertions
    emission_patterns = [
        (r'(scope1[_\s]*(?:total)?["\']?\s*[:\]]\s*)([\d\.]+)', 
         lambda m: f'{m.group(1)}create_numeric_fact(parent, "esrs:Scope1Emissions", {m.group(2)}, "current-period", "u-tCO2e")'),
        
        (r'(scope2[_\s]*location["\']?\s*[:\]]\s*)([\d\.]+)',
         lambda m: f'{m.group(1)}create_numeric_fact(parent, "esrs:Scope2LocationBased", {m.group(2)}, "current-period", "u-tCO2e")'),
        
        (r'(scope3[_\s]*(?:total)?["\']?\s*[:\]]\s*)([\d\.]+)',
         lambda m: f'{m.group(1)}create_numeric_fact(parent, "esrs:Scope3Emissions", {m.group(2)}, "current-period", "u-tCO2e")'),
    ]
    
    # Save the patched file
    backup_path = file_path + ".backup_pre_ixbrl"
    if not os.path.exists(backup_path):
        os.rename(file_path, backup_path)
        print(f"✅ Created backup: {backup_path}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Patched esrs_e1_full.py with iXBRL functions!")
    print("\n⚠️  Important: You still need to:")
    print("1. Find where emission values are displayed in HTML")
    print("2. Replace plain text with create_numeric_fact() calls")
    print("3. Add proper context and unit references")
    print("\nExample usage:")
    print('  create_numeric_fact(td_element, "esrs:Scope1Emissions", 1500.0, "current-period", "u-tCO2e")')

if __name__ == "__main__":
    patch_esrs_e1_full()