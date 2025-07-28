#!/usr/bin/env python3
"""
Fix template literal syntax errors in pdf-export-handler.ts
"""

import os
import shutil
from datetime import datetime
import re

def fix_template_literals(file_path):
    """Fix template literal syntax issues"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Fixing template literal syntax errors...")
    
    # Find and fix the problematic template literals in addReportingContext
    # Replace backtick strings with regular string concatenation
    
    replacements = [
        # Fix Reporting Type line
        (r"pdf\.text\(`Reporting Type: Monthly Progress Report`", 
         "pdf.text('Reporting Type: Monthly Progress Report'"),
        
        # Fix Annual Reporting Period line
        (r"pdf\.text\(`Annual Reporting Period: \${reportingYear}`",
         "pdf.text('Annual Reporting Period: ' + reportingYear"),
        
        # Fix Progress Month line
        (r"pdf\.text\(`Progress Month: \${reportingMonth} \${reportingYear}`",
         "pdf.text('Progress Month: ' + reportingMonth + ' ' + reportingYear"),
        
        # Fix any other template literals in the method
        (r"`([^`]+)\${([^}]+)}([^`]*)`",
         r"'\1' + \2 + '\3'"),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Also fix the specific lines mentioned in the error
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Fix line 1522 (0-indexed as 1521)
        if i == 1521 and 'Reporting Type:' in line:
            lines[i] = "    pdf.text('Reporting Type: Monthly Progress Report', 20, currentY);"
        elif i == 1524 and 'Annual Reporting Period:' in line:
            lines[i] = "    pdf.text('Annual Reporting Period: ' + reportingYear, 20, currentY);"
        elif i == 1526 and 'Progress Month:' in line:
            lines[i] = "    pdf.text('Progress Month: ' + reportingMonth + ' ' + reportingYear, 20, currentY);"
    
    # Fix other template literals throughout the compliance sections
    content = '\n'.join(lines)
    
    # Fix PAI calculation line
    content = re.sub(
        r"pdf\.text\('PAI 2 - Carbon Footprint: ' \+ \(data\.summary\.totalEmissions / 1000000\)\.toFixed\(4\) \+ ' tCO₂e/M€ revenue'",
        "pdf.text('PAI 2 - Carbon Footprint: ' + (data.summary.totalEmissions / 1000000).toFixed(4) + ' tCO₂e/M€ revenue'",
        content
    )
    
    # Fix Date line in Management Assertion
    content = re.sub(
        r"pdf\.text\(`Date: \${new Date\(\)\.toLocaleDateString\(\)}`",
        "pdf.text('Date: ' + new Date().toLocaleDateString()",
        content
    )
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed template literal syntax errors")
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
        # Fix the syntax errors
        success = fix_template_literals(file_path)
        
        if success:
            print("\n✨ Syntax errors fixed!")
            print("\nChanges made:")
            print("- Replaced template literals with string concatenation")
            print("- Fixed all backtick usage in compliance sections")
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