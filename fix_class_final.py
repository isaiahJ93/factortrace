#!/usr/bin/env python3
"""
Fix the class structure completely - ensure all methods are properly inside the class
"""

import os
import shutil
from datetime import datetime

def fix_class_structure_completely(file_path):
    """Completely fix the class structure"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Analyzing and fixing class structure...")
    
    # Find the PDFExportHandler class start
    class_start_line = None
    for i, line in enumerate(lines):
        if 'export class PDFExportHandler' in line:
            class_start_line = i
            print(f"✅ Found class start at line {i + 1}")
            break
    
    if class_start_line is None:
        print("❌ Could not find PDFExportHandler class")
        return False
    
    # Track braces to find where the class should end
    brace_count = 0
    class_end_line = None
    for i in range(class_start_line, len(lines)):
        brace_count += lines[i].count('{')
        brace_count -= lines[i].count('}')
        
        if brace_count == 0 and i > class_start_line:
            # This should be the class closing brace
            class_end_line = i
            print(f"✅ Found class end at line {i + 1}")
            break
    
    # Collect all content that should be inside the class
    class_methods = []
    current_line = class_start_line + 1
    
    # Find all methods that should be in the class
    while current_line < len(lines):
        line = lines[current_line].strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('//') or line.startswith('/*'):
            current_line += 1
            continue
        
        # If we find a private method, it should be inside the class
        if line.startswith('private '):
            # Check if this is before the class end
            if class_end_line and current_line > class_end_line:
                print(f"⚠️  Found method outside class at line {current_line + 1}")
                # This method needs to be moved inside
                method_lines = []
                method_brace_count = 0
                method_start = current_line
                
                # Collect the entire method
                while current_line < len(lines):
                    method_lines.append(lines[current_line])
                    method_brace_count += lines[current_line].count('{')
                    method_brace_count -= lines[current_line].count('}')
                    
                    if method_brace_count == 0 and '{' in ''.join(method_lines):
                        current_line += 1
                        break
                    current_line += 1
                
                class_methods.extend(method_lines)
                
                # Remove these lines from their current position
                del lines[method_start:current_line]
                current_line = method_start
            else:
                current_line += 1
        elif line.startswith('export ') and 'function' in line:
            # We've reached export functions, stop processing
            break
        else:
            current_line += 1
    
    # If we found methods to move, insert them before the class closing brace
    if class_methods:
        print(f"🔧 Moving {len(class_methods)} lines inside the class")
        
        # Find the current class end again (it may have shifted)
        brace_count = 0
        for i in range(class_start_line, len(lines)):
            brace_count += lines[i].count('{')
            brace_count -= lines[i].count('}')
            
            if brace_count == 0 and i > class_start_line:
                class_end_line = i
                break
        
        # Insert methods before the closing brace
        for method_line in reversed(class_methods):
            lines.insert(class_end_line, method_line)
    
    # Ensure the file has proper structure
    content = ''.join(lines)
    
    # Check if we need to add closing braces
    total_open = content.count('{')
    total_close = content.count('}')
    
    if total_open > total_close:
        print(f"⚠️  Missing {total_open - total_close} closing braces")
        content = content.rstrip() + '\n' + ('}' * (total_open - total_close)) + '\n'
    
    # Ensure export function exists
    if 'export async function generatePDFReport' not in content:
        export_function = '''

/**
 * Generate PDF report from emission data
 */
export async function generatePDFReport(
  data: PDFExportData,
  options?: { useBackend?: boolean; filename?: string; compress?: boolean; validate?: boolean }
): Promise<ExportResult> {
  const handler = PDFExportHandler.getInstance();
  return handler.exportSinglePDF(data, options);
}
'''
        content += export_function
        print("✅ Added export function")
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Class structure fixed")
    return True

def verify_file_structure(file_path):
    """Verify the file structure is correct"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    print("\n🔍 Verifying file structure...")
    
    # Check for basic structure elements
    has_class = 'export class PDFExportHandler' in content
    has_export_function = 'export async function generatePDFReport' in content
    
    print(f"✓ Has PDFExportHandler class: {has_class}")
    print(f"✓ Has generatePDFReport function: {has_export_function}")
    
    # Check brace balance
    open_braces = content.count('{')
    close_braces = content.count('}')
    print(f"✓ Brace balance: {open_braces} open, {close_braces} close")
    
    # Check for methods outside class
    class_end = None
    brace_count = 0
    class_started = False
    
    for i, line in enumerate(lines):
        if 'export class PDFExportHandler' in line:
            class_started = True
        
        if class_started:
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if brace_count == 0 and '{' in line:
                class_end = i
                break
    
    if class_end:
        # Check for private methods after class end
        methods_outside = []
        for i in range(class_end + 1, len(lines)):
            if 'private ' in lines[i] and '(' in lines[i]:
                methods_outside.append(i + 1)
        
        if methods_outside:
            print(f"⚠️  Found {len(methods_outside)} methods outside class at lines: {methods_outside}")
            return False
        else:
            print("✓ All methods are inside the class")
    
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
        # Fix the class structure
        success1 = fix_class_structure_completely(file_path)
        
        # Verify the structure
        success2 = verify_file_structure(file_path)
        
        if success1 and success2:
            print("\n✨ Successfully fixed class structure!")
            print("\n🚀 Try building again: npm run dev")
        else:
            print("\n⚠️  Manual intervention may be needed")
            print("The file structure has been improved but may need additional fixes")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()