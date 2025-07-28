#!/usr/bin/env python3
"""
Fix undefined rightText variable
"""

import os
import shutil
from datetime import datetime

def fix_rightText_variable(file_path):
    """Fix the undefined rightText variable"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Fixing undefined rightText variable...")
    
    # Find the line with rightText (around line 747)
    for i in range(min(740, len(lines)-1), min(755, len(lines))):
        if 'rightText' in lines[i] and 'pdf.text(rightText' in lines[i]:
            print(f"Found rightText usage at line {i+1}")
            
            # Add rightText definition before this line
            # Look backwards to find where to insert it
            insert_line = i
            for j in range(i-1, max(i-10, 0), -1):
                if 'pageWidth' in lines[j] or 'const' in lines[j] or 'let' in lines[j]:
                    insert_line = j + 1
                    break
            
            # Insert the rightText definition
            rightText_definition = "    const rightText = `${data.reportId || 'GHG-' + Date.now().toString(36).toUpperCase()} | ${new Date().toLocaleDateString()}`;\n"
            lines.insert(insert_line, rightText_definition)
            print(f"✅ Added rightText definition at line {insert_line + 1}")
            break
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return True

def fix_all_undefined_variables(file_path):
    """Fix any other undefined variables in the file"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Checking for other undefined variables...")
    
    # Check if pageWidth and pageHeight are defined where rightText is used
    import re
    
    # Find the addHeader method
    header_match = re.search(r'private addHeader\([^{]+\{([^}]+rightText[^}]+)\}', content, re.DOTALL)
    
    if header_match:
        method_content = header_match.group(1)
        
        # Check if pageWidth is defined
        if 'pageWidth' in method_content and 'const pageWidth' not in method_content:
            # Add pageWidth definition
            content = content.replace(
                'private addHeader(pdf: jsPDF, data: PDFExportData): void {',
                '''private addHeader(pdf: jsPDF, data: PDFExportData): void {
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();'''
            )
            print("✅ Added pageWidth and pageHeight definitions")
    
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
        # Fix the undefined variables
        success1 = fix_rightText_variable(file_path)
        success2 = fix_all_undefined_variables(file_path)
        
        if success1 and success2:
            print("\n✨ Fixed undefined variable errors!")
            print("\nFixed:")
            print("- Added rightText definition")
            print("- Added pageWidth/pageHeight if needed")
            print("\n🚀 Try running again: npm run dev")
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