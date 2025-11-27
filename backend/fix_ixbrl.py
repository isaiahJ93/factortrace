#!/usr/bin/env python3
"""
Fix iXBRL output issues safely using Python
Usage: python fix_ixbrl.py test_output.xhtml fixed_output.xhtml
"""

import re
import sys

def fix_ixbrl_file(input_file, output_file):
    """Fix common iXBRL generation issues"""
    
    print(f"=== FIXING iXBRL FILE ===")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    # Read the entire file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_size = len(content)
    print(f"Original size: {original_size} bytes")
    
    # Fix 1: Remove duplicate head sections
    print("\n1. Removing duplicate <head> sections...")
    head_pattern = re.compile(r'<head>.*?</head>', re.DOTALL)
    heads = list(head_pattern.finditer(content))
    
    if len(heads) > 1:
        print(f"   Found {len(heads)} head sections")
        # Keep only the first head
        second_head_start = heads[1].start()
        second_head_end = heads[1].end()
        content = content[:second_head_start] + content[second_head_end:]
        print(f"   Removed duplicate head at position {second_head_start}")
    
    # Fix 2: Remove empty name attributes
    print("\n2. Removing empty name attributes...")
    empty_names = content.count(' name=""')
    content = content.replace(' name=""', '')
    print(f"   Removed {empty_names} empty name attributes")
    
    # Fix 3: Fix unit references
    print("\n3. Fixing unit references...")
    replacements = [
        ('unitRef="u-tCO2e"', 'unitRef="tCO2e"'),
        ('unitRef="u-MWh"', 'unitRef="MWh"'),
        ('unitRef="u-EUR"', 'unitRef="EUR"'),
        ('unitRef="u-percent"', 'unitRef="percent"'),
        ('unitRef="u-EUR-millions"', 'unitRef="EUR"')
    ]
    
    for old, new in replacements:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            print(f"   Replaced {count} instances of {old}")
    
    # Fix 4: Remove duplicate period dates
    print("\n4. Fixing duplicate period dates...")
    # Pattern for duplicate dates in periods
    dup_pattern = re.compile(
        r'(<xbrli:startDate>([^<]+)</xbrli:startDate>\s*'
        r'<xbrli:endDate>([^<]+)</xbrli:endDate>\s*)'
        r'<xbrli:startDate>[^<]*</xbrli:startDate>\s*'
        r'<xbrli:endDate>[^<]*</xbrli:endDate>',
        re.MULTILINE
    )
    
    matches = dup_pattern.findall(content)
    if matches:
        content = dup_pattern.sub(r'\1', content)
        print(f"   Fixed {len(matches)} duplicate date entries")
    
    # Fix 5: Remove empty date tags
    print("\n5. Removing empty date tags...")
    empty_dates = [
        '<xbrli:startDate />',
        '<xbrli:endDate />',
        '<xbrli:startDate/>',
        '<xbrli:endDate/>'
    ]
    
    for empty_date in empty_dates:
        count = content.count(empty_date)
        if count > 0:
            content = content.replace(empty_date, '')
            print(f"   Removed {count} instances of {empty_date}")
    
    # Fix 6: Fix misplaced ix:header
    print("\n6. Checking ix:header placement...")
    # ix:header should not be inside <head> tag
    head_match = re.search(r'<head>.*?</head>', content, re.DOTALL)
    if head_match and '<ix:header>' in head_match.group():
        print("   WARNING: ix:header found inside <head> tag - this needs manual fixing")
    
    # Fix 7: Add missing fact names for key emissions
    print("\n7. Adding missing energy fact names...")
    # This is a targeted fix for the energy section
    energy_section = re.search(
        r'<section class="energy-consumption".*?</section>', 
        content, 
        re.DOTALL
    )
    
    if energy_section:
        section_content = energy_section.group()
        # Count unnamed energy facts
        unnamed_energy = section_content.count('<ix:nonFraction contextRef="c-current" unitRef="MWh"')
        if unnamed_energy > 0:
            print(f"   Found {unnamed_energy} unnamed energy facts - please add names manually")
    
    # Write the fixed content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    final_size = len(content)
    print(f"\n=== SUMMARY ===")
    print(f"Original size: {original_size} bytes")
    print(f"Final size: {final_size} bytes")
    print(f"Size difference: {original_size - final_size} bytes removed")
    
    # Verify the output
    print(f"\n=== VERIFICATION ===")
    with open(output_file, 'r', encoding='utf-8') as f:
        verify_content = f.read()
    
    print(f"Head tags: {verify_content.count('<head>')}")
    print(f"Empty names: {verify_content.count(' name=\"\"')}")
    print(f"Valid facts: {len(re.findall(r'name=\"esrs:[^\"]*\"', verify_content))}")
    print(f"Wrong units: {verify_content.count('unitRef=\"u-')}")
    
    # Check for basic XML structure
    if verify_content.startswith('<?xml') and '<html' in verify_content and '</html>' in verify_content:
        print("✅ Basic XML structure looks good")
    else:
        print("❌ WARNING: XML structure may be corrupted")
    
    print(f"\nRun validation with:")
    print(f"poetry run arelleCmdLine --file {output_file} --validate")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_ixbrl.py input.xhtml output.xhtml")
        sys.exit(1)
    
    fix_ixbrl_file(sys.argv[1], sys.argv[2])