#!/usr/bin/env python3
"""
Fix ESRS methods placement - move them inside the PDFExportHandler class
"""

import os
import shutil
from datetime import datetime
import re

def fix_methods_placement(file_path):
    """Move ESRS methods inside the class and fix interface"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Analyzing file structure...")
    
    # Find the PDFExportHandler class boundaries
    class_match = re.search(r'(export class PDFExportHandler\s*\{)', content)
    if not class_match:
        print("❌ Could not find PDFExportHandler class")
        return False
    
    class_start = class_match.start()
    print(f"✅ Found class start at position {class_start}")
    
    # Find the actual end of the class by counting braces
    brace_count = 0
    in_string = False
    escape_next = False
    class_end = None
    
    for i in range(class_start, len(content)):
        char = content[i]
        
        # Handle string literals
        if not escape_next:
            if char in ['"', "'", '`'] and not in_string:
                in_string = char
            elif char == in_string:
                in_string = False
            elif char == '\\':
                escape_next = True
        else:
            escape_next = False
        
        # Count braces only outside strings
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    class_end = i
                    break
    
    if class_end is None:
        print("❌ Could not find class end")
        return False
    
    print(f"✅ Found class end at position {class_end}")
    
    # Find the ESRS methods section
    esrs_match = re.search(r'(\n\s*//\s*=+\s*\n\s*//\s*ESRS E1 Enhanced Section Methods[\s\S]*?)(\n}\s*\n\s*(?:export|/\*\*|$))', content)
    
    if not esrs_match:
        print("❌ Could not find ESRS methods section")
        return False
    
    esrs_methods = esrs_match.group(1)
    esrs_start = esrs_match.start()
    esrs_end = esrs_match.end(1)
    
    print(f"✅ Found ESRS methods from position {esrs_start} to {esrs_end}")
    
    # Check if methods are outside the class
    if esrs_start > class_end:
        print("❌ ESRS methods are OUTSIDE the class - fixing...")
        
        # Remove methods from their current location
        content = content[:esrs_start] + content[esrs_end:]
        
        # Find where to insert them (just before the class closing brace)
        # We need to recalculate class_end after removal
        class_match = re.search(r'(export class PDFExportHandler\s*\{)', content)
        class_start = class_match.start()
        
        # Find class end again
        brace_count = 0
        in_string = False
        for i in range(class_start, len(content)):
            char = content[i]
            if not in_string:
                if char in ['"', "'", '`']:
                    in_string = char
                elif char == in_string:
                    in_string = False
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        class_end = i
                        break
        
        # Insert methods before the class closing brace
        content = content[:class_end] + esrs_methods + '\n' + content[class_end:]
        print("✅ Moved ESRS methods inside the class")
    else:
        print("✅ ESRS methods are already inside the class")
    
    # Fix the PDFExportData interface
    print("\n🔧 Updating PDFExportData interface...")
    
    # Find the interface
    interface_match = re.search(r'(export interface PDFExportData\s*\{)([\s\S]*?)(\n\})', content)
    
    if interface_match:
        interface_content = interface_match.group(2)
        
        # Check for missing properties
        missing_props = []
        if 'dataQuality' not in interface_content:
            missing_props.append('  dataQuality?: DataQualityMetrics;')
        if 'esrsE1Data' not in interface_content:
            missing_props.append('  esrsE1Data?: any;')
        if 'ghgBreakdown' not in interface_content:
            missing_props.append('  ghgBreakdown?: any;')
        if 'uncertaintyAnalysis' not in interface_content:
            missing_props.append('  uncertaintyAnalysis?: any;')
        if 'results' not in interface_content:
            missing_props.append('  results?: any;')
        
        if missing_props:
            # Add missing properties
            new_interface_content = interface_content + '\n' + '\n'.join(missing_props)
            content = content[:interface_match.start()] + \
                     interface_match.group(1) + new_interface_content + \
                     interface_match.group(3) + content[interface_match.end():]
            print(f"✅ Added {len(missing_props)} missing properties to PDFExportData")
    
    # Fix spread operator issues with DESIGN colors
    print("\n🔧 Fixing spread operator issues...")
    
    # Replace spread operators with explicit arrays
    replacements = [
        (r'\.\.\.DESIGN\.colors\.primary\b', 'DESIGN.colors.primary[0], DESIGN.colors.primary[1], DESIGN.colors.primary[2]'),
        (r'\.\.\.DESIGN\.colors\.secondary\b', 'DESIGN.colors.secondary[0], DESIGN.colors.secondary[1], DESIGN.colors.secondary[2]'),
        (r'\.\.\.DESIGN\.colors\.text\b', 'DESIGN.colors.text[0], DESIGN.colors.text[1], DESIGN.colors.text[2]'),
        (r'\.\.\.DESIGN\.colors\.success\b', 'DESIGN.colors.success[0], DESIGN.colors.success[1], DESIGN.colors.success[2]'),
        (r'\.\.\.DESIGN\.colors\.warning\b', 'DESIGN.colors.warning[0], DESIGN.colors.warning[1], DESIGN.colors.warning[2]'),
        (r'\.\.\.DESIGN\.colors\.error\b', 'DESIGN.colors.error[0], DESIGN.colors.error[1], DESIGN.colors.error[2]'),
    ]
    
    for pattern, replacement in replacements:
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            print(f"  ✅ Fixed {count} instances of {pattern}")
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ All fixes applied successfully!")
    return True

def main():
    """Main function"""
    expected_dir = "/Users/isaiah/Documents/Scope3Tool"
    current_dir = os.getcwd()
    
    if current_dir != expected_dir:
        try:
            os.chdir(expected_dir)
        except Exception as e:
            print(f"❌ Could not change directory: {e}")
            return
    
    file_path = "./factortrace-frontend/src/components/emissions/pdf-export-handler.ts"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📁 Processing: {file_path}")
    
    # Create backup
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    try:
        # Fix the file
        success = fix_methods_placement(file_path)
        
        if success:
            print("\n✨ File fixed successfully!")
            print("\nChanges made:")
            print("1. Moved ESRS methods inside the PDFExportHandler class")
            print("2. Added missing properties to PDFExportData interface")
            print("3. Fixed spread operator syntax for TypeScript compatibility")
            print("\n🚀 Try building again: npm run dev")
        else:
            print("\n❌ Fix failed!")
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, file_path)
    except Exception as e:
        print(f"\n❌ Error during fix: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()