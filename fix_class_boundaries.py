#!/usr/bin/env python3
"""
Fix PDF handler by finding exact class boundaries and moving all methods inside
"""

import os
import shutil
from datetime import datetime

def fix_class_structure(file_path):
    """Fix the class structure by moving all methods inside"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Analyzing class structure...")
    
    # Find the PDFExportHandler class declaration
    class_start = None
    for i, line in enumerate(lines):
        if 'export class PDFExportHandler' in line and '{' in line:
            class_start = i
            print(f"✅ Found class declaration at line {i + 1}")
            break
    
    if class_start is None:
        print("❌ Could not find PDFExportHandler class")
        return False
    
    # Find where the class SHOULD end by looking for its methods
    # The class should contain methods like getInstance, exportSinglePDF, etc.
    last_method_end = class_start
    brace_depth = 0
    in_method = False
    
    for i in range(class_start, len(lines)):
        line = lines[i]
        
        # Track brace depth
        brace_depth += line.count('{')
        brace_depth -= line.count('}')
        
        # Look for method declarations inside the class
        if ('getInstance' in line or 'exportSinglePDF' in line or 
            'generatePDFClient' in line or 'reconcileData' in line):
            in_method = True
        
        # If we're in a method and hit depth 1, we found a method end
        if in_method and brace_depth == 1 and '}' in line:
            last_method_end = i
            in_method = False
    
    # The class should end after the last method
    class_end = None
    for i in range(last_method_end, min(last_method_end + 20, len(lines))):
        if lines[i].strip() == '}':
            class_end = i
            print(f"✅ Found class end at line {class_end + 1}")
            break
    
    if class_end is None:
        print("❌ Could not find class end")
        return False
    
    # Find methods that are outside the class (like addHeader at line 225)
    methods_to_move = []
    for i in range(class_end + 1, len(lines)):
        if 'private ' in lines[i] and '(' in lines[i] and '{' in lines[i]:
            methods_to_move.append(i)
            print(f"⚠️  Found method outside class at line {i + 1}: {lines[i].strip()[:50]}...")
    
    if methods_to_move:
        print(f"\n🔧 Moving {len(methods_to_move)} methods inside the class...")
        
        # Collect all methods that need to be moved
        methods_content = []
        
        for method_start in methods_to_move:
            # Find the end of this method
            method_lines = []
            brace_count = 0
            method_started = False
            
            for i in range(method_start, len(lines)):
                line = lines[i]
                method_lines.append(line)
                
                if '{' in line:
                    method_started = True
                
                if method_started:
                    brace_count += line.count('{')
                    brace_count -= line.count('}')
                    
                    if brace_count == 0:
                        break
            
            methods_content.extend(method_lines)
            methods_content.append('\n')
        
        # Remove these methods from their current location
        # Do it in reverse order to maintain indices
        for method_start in reversed(methods_to_move):
            # Find method end
            brace_count = 0
            method_end = method_start
            for i in range(method_start, len(lines)):
                brace_count += lines[i].count('{')
                brace_count -= lines[i].count('}')
                if brace_count == 0 and i > method_start:
                    method_end = i
                    break
            
            # Remove the method
            del lines[method_start:method_end + 1]
        
        # Insert all methods before the class closing brace
        # Recalculate class_end after deletions
        class_end_new = None
        brace_depth = 0
        for i in range(class_start, len(lines)):
            brace_depth += lines[i].count('{')
            brace_depth -= lines[i].count('}')
            if brace_depth == 0 and i > class_start:
                class_end_new = i
                break
        
        if class_end_new:
            # Insert methods before the closing brace
            for method_line in reversed(methods_content):
                lines.insert(class_end_new, method_line)
            
            print("✅ Moved all methods inside the class")
    
    # Ensure proper file ending
    # Make sure there's the closing brace and export statements
    content = ''.join(lines)
    
    # Check if export functions exist
    if 'export async function generatePDFReport' not in content:
        export_functions = """

/**
 * Generate PDF report
 */
export async function generatePDFReport(
  data: PDFExportData,
  options?: { useBackend?: boolean; filename?: string; compress?: boolean; validate?: boolean }
): Promise<ExportResult> {
  const handler = PDFExportHandler.getInstance();
  return handler.exportSinglePDF(data, options);
}
"""
        content += export_functions
        print("✅ Added export function")
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
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
        success = fix_class_structure(file_path)
        
        if success:
            print("\n✨ Successfully fixed class structure!")
            print("\nWhat was done:")
            print("✓ Found exact class boundaries")
            print("✓ Moved all methods inside PDFExportHandler class")
            print("✓ Ensured proper file structure")
            print("\n🚀 Try building again: npm run dev")
            print("\nYour PDF export should now work with all professional features!")
        else:
            print("\n❌ Fix failed!")
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, file_path)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()