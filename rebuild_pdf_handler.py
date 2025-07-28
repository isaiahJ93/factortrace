#!/usr/bin/env python3
"""
Reconstruct the PDF handler with correct structure
"""

import os
import shutil
from datetime import datetime
import re

def extract_methods_and_rebuild(file_path):
    """Extract all methods and rebuild the file with correct structure"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Extracting methods and rebuilding file...")
    
    # Extract imports and interfaces
    imports_match = re.search(r'^(import[\s\S]*?)(?=export)', content, re.MULTILINE)
    imports = imports_match.group(1) if imports_match else ''
    
    # Extract DESIGN constant if it exists
    design_match = re.search(r'(const DESIGN = \{[\s\S]*?\n\};)', content)
    design_const = design_match.group(1) if design_match else ''
    
    # Extract interfaces
    interface_matches = re.findall(r'(export interface \w+[\s\S]*?\n\})', content)
    interfaces = '\n\n'.join(interface_matches)
    
    # Extract all methods (both inside and outside class)
    method_pattern = r'(private (?:async )?\w+\([^)]*\)(?::\s*\w+(?:<[^>]+>)?)?\s*\{[\s\S]*?\n  \})'
    all_methods = re.findall(method_pattern, content)
    
    print(f"Found {len(all_methods)} methods")
    
    # Build the new file structure
    new_content = imports.strip() + '\n\n'
    
    if design_const:
        new_content += design_const + '\n\n'
    
    new_content += interfaces + '\n\n'
    
    # Build the class
    new_content += '''/**
 * PDF Export Handler for ESRS E1 compliant reports
 */
export class PDFExportHandler {
  private static instance: PDFExportHandler;
  private readonly apiUrl: string;
  
  private constructor(apiUrl: string = 'http://localhost:8000') {
    this.apiUrl = apiUrl;
  }
  
  public static getInstance(apiUrl?: string): PDFExportHandler {
    if (!PDFExportHandler.instance) {
      PDFExportHandler.instance = new PDFExportHandler(apiUrl);
    }
    return PDFExportHandler.instance;
  }
'''
    
    # Add each method to the class
    for method in all_methods:
        # Clean up the method indentation
        method_lines = method.split('\n')
        cleaned_method = '\n'.join('  ' + line if line.strip() else '' for line in method_lines)
        new_content += '\n' + cleaned_method + '\n'
    
    # Close the class
    new_content += '}\n\n'
    
    # Add the export function
    export_func_match = re.search(r'(export async function generatePDFReport[\s\S]*?\n\})', content)
    if export_func_match:
        new_content += export_func_match.group(1) + '\n'
    else:
        new_content += '''/**
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
    
    # Write the rebuilt content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ File rebuilt with correct structure")
    return True

def verify_structure(file_path):
    """Verify the file structure is correct"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Verifying structure...")
    
    # Check for class
    if 'export class PDFExportHandler {' not in content:
        print("❌ Missing class declaration")
        return False
    
    # Check that no private methods are outside the class
    class_end = content.find('}\n\nexport')
    if class_end == -1:
        class_end = content.rfind('}\n\n/**')
    
    if class_end != -1:
        after_class = content[class_end:]
        if 'private ' in after_class:
            print("❌ Found private methods outside class")
            return False
    
    # Check brace balance
    open_braces = content.count('{')
    close_braces = content.count('}')
    
    print(f"Brace count: {open_braces} open, {close_braces} close")
    
    if open_braces != close_braces:
        print(f"⚠️  Brace mismatch!")
        return False
    
    print("✅ Structure verified")
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
        # Rebuild the file
        success1 = extract_methods_and_rebuild(file_path)
        
        # Verify structure
        success2 = verify_structure(file_path)
        
        if success1 and success2:
            print("\n✨ Successfully rebuilt PDF handler!")
            print("\nThe file now has:")
            print("✓ All imports at the top")
            print("✓ All methods inside the PDFExportHandler class")
            print("✓ Export function at the bottom")
            print("✓ Correct structure throughout")
            print("\n🚀 Try building again: npm run dev")
        else:
            print("\n❌ Rebuild may have issues")
            print("Check the file manually")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()