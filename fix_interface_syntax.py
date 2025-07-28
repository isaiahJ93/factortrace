#!/usr/bin/env python3
"""
Fix interface syntax error in PDF export handler
"""

import os
import shutil
from datetime import datetime
import re

def fix_interface_syntax(file_path):
    """Fix the interface syntax error"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Fixing interface syntax error...")
    
    # Look for the problematic interface around line 35
    for i in range(30, min(40, len(lines))):
        if 'export interface PDFExportData' in lines[i]:
            print(f"Found interface at line {i + 1}")
            # Make sure it has proper syntax
            lines[i] = 'export interface PDFExportData {\n'
            print("✅ Fixed interface declaration")
            break
    
    # Check for any other malformed syntax around that area
    # The error suggests something is wrong with the structure
    
    # Ensure proper structure of the interface
    interface_start = None
    interface_end = None
    
    for i, line in enumerate(lines):
        if 'export interface PDFExportData' in line:
            interface_start = i
        elif interface_start is not None and line.strip() == '}' and interface_end is None:
            # Check if this is the end of the interface
            # Count braces from interface start
            brace_count = 0
            for j in range(interface_start, i + 1):
                brace_count += lines[j].count('{')
                brace_count -= lines[j].count('}')
            if brace_count == 0:
                interface_end = i
                break
    
    if interface_start is not None and interface_end is not None:
        print(f"Interface spans lines {interface_start + 1} to {interface_end + 1}")
        
        # Make sure the interface is properly formatted
        # Check if there's proper content
        interface_content = ''.join(lines[interface_start:interface_end + 1])
        
        if 'metadata:' not in interface_content:
            # The interface might be empty or malformed
            print("⚠️  Interface appears to be malformed - rebuilding it")
            
            # Replace with a proper interface
            proper_interface = '''export interface PDFExportData {
  metadata: {
    documentId?: string;
    companyName: string;
    reportingPeriod: string;
    generatedDate: string;
    standard?: string;
    methodology?: string;
  };
  summary: {
    totalEmissions: number;
    scope1: number;
    scope2: number;
    scope3: number;
    scope1Percentage?: number;
    scope2Percentage?: number;
    scope3Percentage?: number;
    dataQualityScore?: number;
  };
  governance?: any;
  targets?: any[];
  activities?: any[];
  scope3Categories?: any[];
  topEmissionSources?: any[];
  [key: string]: any;
}
'''
            # Replace the malformed interface
            interface_lines = proper_interface.split('\n')
            
            # Remove old interface lines
            del lines[interface_start:interface_end + 1]
            
            # Insert new interface
            for j, new_line in enumerate(interface_lines):
                lines.insert(interface_start + j, new_line + '\n')
            
            print("✅ Rebuilt PDFExportData interface")
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return True

def check_file_structure(file_path):
    """Check and fix overall file structure"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Checking file structure...")
    
    # Ensure imports are at the top
    if not content.startswith('import'):
        print("⚠️  File doesn't start with imports")
        
        # Add necessary imports
        imports = '''import jsPDF from 'jspdf';
import 'jspdf-autotable';

'''
        content = imports + content
        print("✅ Added imports")
    
    # Check for other required interfaces
    if 'export interface ExportResult' not in content:
        print("⚠️  Missing ExportResult interface")
        
        # Add it after PDFExportData
        export_result_interface = '''
export interface ExportResult {
  success: boolean;
  blob: Blob | null;
  error?: string;
}
'''
        # Find where to insert it
        pdf_export_data_end = content.find('}\n', content.find('export interface PDFExportData'))
        if pdf_export_data_end != -1:
            content = content[:pdf_export_data_end + 2] + export_result_interface + content[pdf_export_data_end + 2:]
            print("✅ Added ExportResult interface")
    
    # Write the updated content
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
        # Fix interface syntax
        success1 = fix_interface_syntax(file_path)
        
        # Check overall structure
        success2 = check_file_structure(file_path)
        
        if success1 and success2:
            print("\n✨ Successfully fixed interface syntax!")
            print("\nFixed:")
            print("✓ PDFExportData interface declaration")
            print("✓ Added missing interfaces if needed")
            print("✓ Ensured proper file structure")
            print("\n🚀 Try building again: npm run dev")
        else:
            print("\n❌ Fix may be incomplete")
            print("Check the build output for more details")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()