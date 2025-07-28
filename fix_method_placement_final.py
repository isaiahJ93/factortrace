#!/usr/bin/env python3
"""
Fix the addHeader placement - ensure it's inside the class
"""

import os
import shutil
from datetime import datetime
import re

def fix_method_placement(file_path):
    """Fix the placement of methods - ensure they're all inside the class"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Fixing method placement...")
    
    # First, fix the generatePDFReport function syntax
    # It seems to be missing closing parentheses
    content = re.sub(
        r'(export async function generatePDFReport\([^)]+)(\n\s*private)',
        r'\1): Promise<ExportResult> {\n  const handler = PDFExportHandler.getInstance();\n  return handler.exportSinglePDF(data, options);\n}\n\n// Methods below should be in the class',
        content
    )
    
    # Find the PDFExportHandler class
    class_match = re.search(r'export class PDFExportHandler \{([\s\S]*?)(\n\})\s*(?=\n(?:export|/\*|$))', content)
    
    if not class_match:
        print("❌ Could not find PDFExportHandler class boundaries")
        return False
    
    class_content = class_match.group(1)
    class_end_pos = class_match.end(1)
    
    # Find all methods that are outside the class
    methods_outside_pattern = r'(\n\s*private\s+\w+\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{[\s\S]*?\n\s*\})'
    
    # Get the content after the class
    after_class = content[class_match.end():]
    
    # Find all private methods in the after_class section
    methods_outside = re.findall(methods_outside_pattern, after_class)
    
    if methods_outside:
        print(f"Found {len(methods_outside)} methods outside the class")
        
        # Remove these methods from their current location
        for method in methods_outside:
            after_class = after_class.replace(method, '')
        
        # Add them to the class
        new_class_content = class_content
        for method in methods_outside:
            new_class_content += '\n' + method.strip()
            print(f"  ✅ Moved method into class")
        
        # Rebuild the content
        content = content[:class_match.start()] + 'export class PDFExportHandler {' + new_class_content + '\n}' + after_class
    
    # Ensure the generatePDFReport function is complete
    if 'export async function generatePDFReport' in content:
        # Make sure it has a proper body
        gen_pdf_pattern = r'export async function generatePDFReport\([^)]+\)(?:\s*:\s*Promise<ExportResult>)?\s*\{'
        gen_pdf_match = re.search(gen_pdf_pattern, content)
        
        if gen_pdf_match:
            # Check if it has a body
            start_pos = gen_pdf_match.end()
            # Count braces to find the end
            brace_count = 1
            pos = start_pos
            
            while pos < len(content) and brace_count > 0:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            # Check if the body is empty or too short
            body = content[start_pos:pos-1].strip()
            if len(body) < 50:  # Probably incomplete
                print("🔧 Fixing generatePDFReport function body")
                # Replace with a complete implementation
                complete_function = '''export async function generatePDFReport(
  data: PDFExportData,
  options?: { useBackend?: boolean; filename?: string; compress?: boolean; validate?: boolean }
): Promise<ExportResult> {
  const handler = PDFExportHandler.getInstance();
  return handler.exportSinglePDF(data, options);
}'''
                
                # Find and replace the function
                func_end = content.find('}', gen_pdf_match.start()) + 1
                content = content[:gen_pdf_match.start()] + complete_function + content[func_end:]
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed method placement")
    return True

def verify_structure(file_path):
    """Verify the file structure is correct"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    print("\n🔍 Verifying structure...")
    
    # Check for methods outside class
    class_ended = False
    methods_outside = []
    
    for i, line in enumerate(lines):
        if '} // end of PDFExportHandler' in line or (class_ended and 'export' in line and 'function' in line):
            class_ended = True
        
        if class_ended and 'private ' in line and '(' in line:
            methods_outside.append(i + 1)
    
    if methods_outside:
        print(f"⚠️  Still found methods outside class at lines: {methods_outside}")
        return False
    
    print("✅ All methods are inside the class")
    
    # Check brace balance
    open_braces = content.count('{')
    close_braces = content.count('}')
    
    if open_braces != close_braces:
        print(f"⚠️  Brace mismatch: {open_braces} open, {close_braces} close")
        return False
    
    print("✅ Brace balance is correct")
    
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
        # Fix method placement
        success1 = fix_method_placement(file_path)
        
        # Verify structure
        success2 = verify_structure(file_path)
        
        if success1 and success2:
            print("\n✨ Successfully fixed method placement!")
            print("\nFixed:")
            print("✓ Moved all methods inside PDFExportHandler class")
            print("✓ Fixed generatePDFReport function syntax")
            print("✓ Verified file structure")
            print("\n🚀 Try building again: npm run dev")
        else:
            print("\n⚠️  Some issues may remain")
            print("Check the build output for details")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()