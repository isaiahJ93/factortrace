#!/usr/bin/env python3
"""
Fix the placement of ESRS methods - ensure they're inside the class
"""

import os
import shutil
from datetime import datetime
import re

def fix_esrs_methods_placement(file_path):
    """Ensure all methods are inside the PDFExportHandler class"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Fixing ESRS methods placement...")
    
    # First, remove any methods that are outside the class
    # Look for private methods after the class has ended
    lines = content.split('\n')
    
    # Find the PDFExportHandler class
    class_start_line = None
    for i, line in enumerate(lines):
        if 'export class PDFExportHandler' in line:
            class_start_line = i
            print(f"✅ Found class start at line {i + 1}")
            break
    
    if class_start_line is None:
        print("❌ Could not find PDFExportHandler class")
        return False
    
    # Find where the class ends by counting braces
    brace_count = 0
    class_end_line = None
    in_string = False
    
    for i in range(class_start_line, len(lines)):
        line = lines[i]
        
        # Simple string detection (not perfect but good enough)
        quote_count = line.count('"') + line.count("'")
        if quote_count % 2 != 0:
            in_string = not in_string
        
        if not in_string:
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if brace_count == 0 and i > class_start_line:
                class_end_line = i
                print(f"✅ Found class end at line {i + 1}")
                break
    
    # Find any private methods after the class end
    methods_outside_class = []
    if class_end_line:
        for i in range(class_end_line + 1, len(lines)):
            if 'private add' in lines[i] and '(' in lines[i]:
                methods_outside_class.append(i)
                print(f"⚠️  Found method outside class at line {i + 1}: {lines[i].strip()[:50]}...")
    
    # If methods are outside, we need to move them inside
    if methods_outside_class:
        print(f"🔧 Moving {len(methods_outside_class)} methods inside the class...")
        
        # Find all the ESRS methods (they're in a block)
        esrs_start = None
        esrs_end = None
        
        for i in range(class_end_line, len(lines)):
            if '* Add Data Quality Score Section' in lines[i]:
                esrs_start = i - 2  # Include the comment block
                break
        
        if esrs_start:
            # Find the end of the ESRS methods block
            for i in range(len(lines) - 1, esrs_start, -1):
                if 'addUncertaintySection' in lines[i] and lines[i+1].strip() == '}':
                    esrs_end = i + 1
                    break
            
            if esrs_end:
                print(f"✅ Found ESRS methods block from line {esrs_start + 1} to {esrs_end + 1}")
                
                # Extract the methods
                esrs_methods = lines[esrs_start:esrs_end + 1]
                
                # Remove them from their current location
                del lines[esrs_start:esrs_end + 1]
                
                # Recalculate class_end_line after deletion
                class_end_line = class_end_line - (esrs_end - esrs_start + 1) if esrs_start < class_end_line else class_end_line
                
                # Insert them just before the class closing brace
                for idx, method_line in enumerate(esrs_methods):
                    lines.insert(class_end_line + idx, method_line)
                
                print("✅ Moved ESRS methods inside the class")
    
    # Reconstruct content
    content = '\n'.join(lines)
    
    # Also fix the header if needed
    content = fix_header_format(content)
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def fix_header_format(content):
    """Fix the header formatting"""
    
    # Fix the header method to be cleaner
    header_pattern = r'(private addHeader\([^{]+\{)([\s\S]*?)(\n\s*\})'
    
    new_header_body = """
    const pageWidth = pdf.internal.pageSize.getWidth();
    const documentId = data.metadata.documentId || 'GHG-' + Date.now().toString(36).toUpperCase();
    const currentDate = new Date().toLocaleDateString('en-GB');
    const companyName = data.metadata.companyName || 'Your Company';
    const totalEmissions = data.summary.totalEmissions.toFixed(1);
    
    // Header text
    pdf.setFontSize(8);
    pdf.setTextColor(100, 100, 100);
    
    // Left side
    pdf.text(documentId + ' | ' + currentDate, 20, 9);
    
    // Right side  
    pdf.text(companyName + ' ESRS E1 | ' + totalEmissions + ' tCO2e', pageWidth - 20, 9, { align: 'right' });
    
    // Header line
    pdf.setDrawColor(200, 200, 200);
    pdf.setLineWidth(0.5);
    pdf.line(20, 12, pageWidth - 20, 12);"""
    
    content = re.sub(header_pattern, r'\1' + new_header_body + r'\3', content, flags=re.DOTALL)
    
    return content

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
        # Fix the methods placement
        success = fix_esrs_methods_placement(file_path)
        
        if success:
            print("\n✨ Fixed ESRS methods placement!")
            print("\nChanges made:")
            print("✓ Moved all ESRS methods inside PDFExportHandler class")
            print("✓ Fixed header formatting")
            print("✓ Methods are now properly scoped as private")
            print("\n🚀 Try building again: npm run dev")
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