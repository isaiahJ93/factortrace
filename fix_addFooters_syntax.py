#!/usr/bin/env python3
"""
Fix the addFooters method syntax error
"""

import os
import shutil
from datetime import datetime
import re

def fix_addFooters_method(file_path):
    """Fix the syntax error in addFooters method"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Fixing addFooters method syntax...")
    
    # Find the addFooters method around line 802
    for i in range(min(795, len(lines)-1), min(810, len(lines))):
        if 'private addFooters' in lines[i]:
            print(f"Found addFooters at line {i + 1}: {lines[i].strip()}")
            
            # The method signature is malformed - fix it
            lines[i] = '  private addFooters(pdf: jsPDF, data: PDFExportData): void {\n'
            print("✅ Fixed method signature")
            break
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return True

def check_class_closure(file_path):
    """Ensure the class is properly closed before this method"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("\n🔍 Checking class structure around addFooters...")
    
    # Find where PDFExportHandler class starts
    class_start = None
    for i, line in enumerate(lines):
        if 'export class PDFExportHandler' in line:
            class_start = i
            break
    
    if class_start is None:
        print("❌ Could not find class start")
        return False
    
    # Count braces from class start to addFooters
    addFooters_line = None
    for i, line in enumerate(lines):
        if 'private addFooters' in line:
            addFooters_line = i
            break
    
    if addFooters_line:
        # Count braces between class start and addFooters
        brace_count = 0
        for i in range(class_start, addFooters_line):
            brace_count += lines[i].count('{')
            brace_count -= lines[i].count('}')
        
        print(f"Brace count from class start to addFooters: {brace_count}")
        
        if brace_count == 0:
            print("⚠️  addFooters is OUTSIDE the class!")
            
            # Find the last method before addFooters
            last_method_end = None
            for i in range(addFooters_line - 1, class_start, -1):
                if lines[i].strip() == '}' and i > class_start + 10:
                    # Check if this is a method closing brace
                    # Look for the opening of this method
                    temp_brace_count = -1
                    for j in range(i - 1, max(i - 50, class_start), -1):
                        temp_brace_count += lines[j].count('}')
                        temp_brace_count -= lines[j].count('{')
                        if temp_brace_count == 0 and 'private' in lines[j]:
                            last_method_end = i
                            break
                    if last_method_end:
                        break
            
            if last_method_end:
                print(f"Found last method end at line {last_method_end + 1}")
                
                # Remove the extra closing brace if there is one
                if lines[last_method_end + 1].strip() == '}':
                    print("🔧 Removing extra closing brace")
                    del lines[last_method_end + 1]
                    
                    # Save the fixed file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    
                    return True
    
    return True

def ensure_all_methods_in_class(file_path):
    """Make sure all methods are inside the class"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Ensuring all methods are inside the class...")
    
    # Find the class declaration and all its methods
    class_pattern = r'export class PDFExportHandler \{([\s\S]*?)(\n\})\s*\n'
    class_match = re.search(class_pattern, content)
    
    if not class_match:
        print("❌ Could not find class with regex")
        return False
    
    class_content = class_match.group(1)
    class_end_pos = class_match.end()
    
    # Find any private methods after the class
    remaining_content = content[class_end_pos:]
    private_methods = re.findall(r'(private \w+[\s\S]*?\n  \})', remaining_content)
    
    if private_methods:
        print(f"⚠️  Found {len(private_methods)} methods outside the class")
        
        # Add them to the class
        new_class_content = class_content
        for method in private_methods:
            new_class_content += '\n\n  ' + method.strip()
            print(f"  ✅ Moving method: {method.split('(')[0].strip()}")
        
        # Remove methods from outside the class
        for method in private_methods:
            remaining_content = remaining_content.replace(method, '')
        
        # Reconstruct the file
        new_content = content[:class_match.start()] + \
                     'export class PDFExportHandler {' + \
                     new_class_content + '\n}' + \
                     remaining_content
        
        # Save the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Moved all methods inside the class")
        return True
    
    print("✅ All methods are already inside the class")
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
        # Fix the addFooters method syntax
        success1 = fix_addFooters_method(file_path)
        
        # Check class closure
        success2 = check_class_closure(file_path)
        
        # Ensure all methods are in the class
        success3 = ensure_all_methods_in_class(file_path)
        
        if success1 and success2 and success3:
            print("\n✨ Successfully fixed the syntax error!")
            print("\n🚀 Try building again: npm run dev")
        else:
            print("\n⚠️  Some issues remain")
            print("Check the build output for more details")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()