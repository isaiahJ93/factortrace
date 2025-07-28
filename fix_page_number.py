#!/usr/bin/env python3
"""
Fix the malformed page number text on line 1502
"""

import os
import shutil
from datetime import datetime

def fix_page_number_line(file_path):
    """Fix the malformed page number line"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Fixing malformed page number line...")
    
    # Fix line 1502 (index 1501)
    if len(lines) > 1501:
        current_line = lines[1501]
        print(f"Current line 1502: {current_line.strip()[:80]}...")
        
        # The line seems to be trying to add page numbers
        # It should be something like:
        # pdf.text('Page ' + i + ' of ' + pageCount, x, y);
        
        # Replace the malformed line with a proper page number display
        lines[1501] = "    pdf.text('Page ' + i + ' of ' + pageCount + '', pageWidth / 2, pageHeight - 20, { align: 'center' });\n"
        print("✅ Fixed page number line")
    
    # Check for any other syntax issues around that area
    for i in range(max(0, 1495), min(len(lines), 1510)):
        line = lines[i]
        
        # Check for lines that have text after semicolons
        if ';' in line and not line.strip().endswith(';'):
            # Get text after semicolon
            after_semi = line.split(';', 1)[1].strip()
            if after_semi and not after_semi.startswith('//'):
                print(f"⚠️  Line {i+1} has text after semicolon: {after_semi[:30]}...")
                # Remove text after semicolon
                lines[i] = line.split(';')[0] + ';\n'
                print(f"  ✅ Cleaned line {i+1}")
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Fixed syntax errors")
    return True

def check_footer_method(file_path):
    """Check and fix the footer method if needed"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Checking footer method...")
    
    # Look for the footer text section and ensure it's properly formatted
    import re
    
    # Fix any malformed footer text
    content = re.sub(
        r"pdf\.text\('Page '\s*\+\s*i\s*\+\s*'[^']*',\s*[^;]+\);\s*of\s*'\s*\+[^;]+",
        "pdf.text('Page ' + i + ' of ' + pageCount, pageWidth / 2, pageHeight - 20, { align: 'center' });",
        content
    )
    
    # Write if changes were made
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Footer method checked")
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
        # Fix the page number line
        success1 = fix_page_number_line(file_path)
        success2 = check_footer_method(file_path)
        
        if success1 and success2:
            print("\n✨ Fixed page number syntax error!")
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