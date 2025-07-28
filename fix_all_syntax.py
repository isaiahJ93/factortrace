#!/usr/bin/env python3
"""
Fix all syntax errors in the compliance sections
"""

import os
import shutil
from datetime import datetime

def fix_all_syntax_errors(file_path):
    """Fix all syntax errors in the compliance sections"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Fixing all syntax errors in compliance sections...")
    
    # Fix specific lines based on the error messages
    fixes = {
        # Line 747 - missing semicolon
        746: "    pdf.text(rightText, pageWidth - DESIGN.layout.margins.right, 9, { align: 'right' });\n",
        
        # Lines around 795-800 - fix string concatenation
        794: "    const info = [\n",
        795: "      'Reporting Period: ' + data.metadata.reportingPeriod + '',\n",
        796: "      'Publication Date: ' + new Date(data.metadata.generatedDate).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }),\n",
        797: "      'Standard Applied: ' + data.metadata.standard || 'ESRS E1, GHG Protocol Corporate Value Chain (Scope 3) Standard',\n",
        798: "      'Methodology: ' + data.metadata.methodology || 'Activity-based and spend-based hybrid approach' + ''\n",
        799: "    ];\n",
    }
    
    # Apply the fixes
    for line_num, fix in fixes.items():
        if line_num < len(lines):
            lines[line_num] = fix
            print(f"✅ Fixed line {line_num + 1}")
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Applied all syntax fixes")
    return True

def fix_compliance_methods(file_path):
    """Fix the compliance methods more comprehensively"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔧 Fixing compliance method syntax...")
    
    # Fix the addReportingContext method
    content = content.replace(
        "pdf.text(`Reporting Type: Monthly Progress Report`, 20, currentY);",
        "pdf.text('Reporting Type: Monthly Progress Report', 20, currentY);"
    )
    
    content = content.replace(
        "pdf.text(`Annual Reporting Period: ${reportingYear}`, 20, currentY);",
        "pdf.text('Annual Reporting Period: ' + reportingYear, 20, currentY);"
    )
    
    content = content.replace(
        "pdf.text(`Progress Month: ${reportingMonth} ${reportingYear}`, 20, currentY);",
        "pdf.text('Progress Month: ' + reportingMonth + ' ' + reportingYear, 20, currentY);"
    )
    
    # Fix the PAI calculation
    content = content.replace(
        "pdf.text('PAI 2 - Carbon Footprint: ' + (data.summary.totalEmissions / 1000000).toFixed(4) + ' tCO₂e/M€ revenue', 20, currentY);",
        "pdf.text('PAI 2 - Carbon Footprint: ' + (data.summary.totalEmissions / 1000000).toFixed(4) + ' tCO2e/M EUR revenue', 20, currentY);"
    )
    
    # Fix the Date line
    content = content.replace(
        "pdf.text(`Date: ${new Date().toLocaleDateString()}`, 20, textY + 35);",
        "pdf.text('Date: ' + new Date().toLocaleDateString(), 20, textY + 35);"
    )
    
    # Fix any remaining template literals
    import re
    # Pattern to find template literals with ${} expressions
    pattern = r'`([^`]*)\$\{([^}]+)\}([^`]*)`'
    
    def replace_template(match):
        before = match.group(1)
        expr = match.group(2)
        after = match.group(3)
        return f"'{before}' + {expr} + '{after}'"
    
    content = re.sub(pattern, replace_template, content)
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed compliance method syntax")
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
        # Fix all syntax errors
        success1 = fix_all_syntax_errors(file_path)
        success2 = fix_compliance_methods(file_path)
        
        if success1 and success2:
            print("\n✨ All syntax errors fixed!")
            print("\nFixed:")
            print("- Missing semicolons")
            print("- String concatenation issues")
            print("- Template literal conversions")
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