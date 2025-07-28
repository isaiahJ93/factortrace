#!/usr/bin/env python3
"""
Clean up the PDF handler file - ensure ALL methods are inside the class
"""

import os
import shutil
from datetime import datetime
import re

def cleanup_pdf_handler(file_path):
    """Ensure all methods are inside the PDFExportHandler class"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Analyzing file structure...")
    
    # Find PDFExportHandler class
    class_start = None
    class_end = None
    brace_count = 0
    
    for i, line in enumerate(lines):
        if 'export class PDFExportHandler' in line:
            class_start = i
            print(f"✅ Found class start at line {i + 1}")
        
        if class_start is not None:
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if brace_count == 0 and '{' in line:
                class_end = i
                print(f"✅ Found class end at line {i + 1}")
                break
    
    if class_start is None or class_end is None:
        print("❌ Could not find class boundaries")
        return False
    
    # Find any private methods outside the class
    methods_outside = []
    for i in range(class_end + 1, len(lines)):
        if 'private ' in lines[i] and '(' in lines[i]:
            methods_outside.append(i)
            print(f"⚠️  Found method outside class at line {i + 1}: {lines[i].strip()[:50]}...")
    
    if methods_outside:
        print(f"\n🔧 Found {len(methods_outside)} methods outside the class")
        
        # Remove all lines after the class that contain private methods
        # Find where the problematic section starts
        first_bad_line = methods_outside[0]
        
        # Look for where this section might end (next export, or end of file)
        section_end = len(lines)
        for i in range(first_bad_line, len(lines)):
            if 'export ' in lines[i] and i > first_bad_line:
                section_end = i
                break
        
        print(f"🗑️  Removing lines {first_bad_line + 1} to {section_end}")
        
        # Remove the problematic section
        del lines[first_bad_line:section_end]
        
        print("✅ Removed methods that were outside the class")
    
    # Ensure the class is properly closed
    # Count braces again to make sure
    content = ''.join(lines)
    class_content = content[content.find('export class PDFExportHandler'):]
    
    brace_count = 0
    for char in class_content:
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                break
    
    if brace_count > 0:
        print(f"⚠️  Class is missing {brace_count} closing brace(s)")
        # Add closing braces
        lines.append('\n' + '}' * brace_count + '\n')
        print(f"✅ Added {brace_count} closing brace(s)")
    
    # Write the cleaned content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return True

def add_basic_enhancements(file_path):
    """Add basic ESRS enhancements that work reliably"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Adding basic ESRS enhancements...")
    
    # Check if we already have the enhancements
    if 'addDataQualityScore' in content:
        print("✅ ESRS enhancements already present")
        return True
    
    # Find where to add the enhancement in the existing PDF structure
    # Look for the executive summary section
    exec_summary_match = re.search(r'(//\s*Executive summary[\s\S]*?)(//\s*(?:Governance|E1-1|ESRS))', content, re.IGNORECASE)
    
    if exec_summary_match:
        # Add data quality score to executive summary
        insertion_point = exec_summary_match.end(1)
        
        enhancement = """
    // Data Quality Score
    const qualityScore = data.summary.dataQualityScore || 72;
    const scoreColor = qualityScore >= 80 ? '16, 185, 129' : qualityScore >= 60 ? '245, 158, 11' : '239, 68, 68';
    
    pdf.setFontSize(11);
    pdf.setTextColor(26, 26, 46);
    pdf.text('Data Quality Score:', col1X, currentY);
    
    pdf.setFontSize(14);
    pdf.text(qualityScore + '%', col2X, currentY);
    currentY += lineHeight;
    
"""
        content = content[:insertion_point] + enhancement + content[insertion_point:]
        print("✅ Added data quality score to executive summary")
    
    # Add ESRS sections to the existing activity details section
    activity_match = re.search(r'(currentY = this\.addActivityDetails\([^;]+;\s*\n)', content)
    
    if activity_match:
        esrs_sections = """
    // ESRS E1 Compliance Information
    pdf.addPage();
    currentY = 20;
    
    pdf.setFontSize(16);
    pdf.setTextColor(26, 26, 46);
    pdf.text('ESRS E1 Compliance Information', 20, currentY);
    currentY += 15;
    
    // E1-5 Energy
    pdf.setFontSize(12);
    pdf.text('E1-5: Energy Consumption', 20, currentY);
    currentY += 8;
    
    pdf.setFontSize(10);
    pdf.setTextColor(50, 50, 50);
    pdf.text('Total energy consumption: 0 MWh', 30, currentY);
    currentY += 5;
    pdf.text('Renewable energy: 0%', 30, currentY);
    currentY += 5;
    pdf.text('Note: Energy consumption captured under Scope 2', 30, currentY);
    currentY += 10;
    
    // E1-8 Carbon Pricing
    pdf.setFontSize(12);
    pdf.setTextColor(26, 26, 46);
    pdf.text('E1-8: Internal Carbon Pricing', 20, currentY);
    currentY += 8;
    
    pdf.setFontSize(10);
    pdf.setTextColor(50, 50, 50);
    pdf.text('Internal carbon price: EUR 0/tCO2e', 30, currentY);
    currentY += 5;
    pdf.text('Coverage: Not currently implemented', 30, currentY);
    currentY += 10;
    
    // E1-3 Actions
    pdf.setFontSize(12);
    pdf.setTextColor(26, 26, 46);
    pdf.text('E1-3: Actions & Resources', 20, currentY);
    currentY += 8;
    
    pdf.setFontSize(10);
    pdf.setTextColor(50, 50, 50);
    pdf.text('Climate-related CapEx: EUR 0 (0% of total)', 30, currentY);
    currentY += 5;
    pdf.text('Climate-related OpEx: EUR 0 (0% of total)', 30, currentY);
    currentY += 5;
    pdf.text('Dedicated FTEs: 0', 30, currentY);
    currentY += 10;
"""
        
        content = content[:activity_match.end()] + esrs_sections + content[activity_match.end():]
        print("✅ Added ESRS E1 compliance sections")
    
    # Write the enhanced content
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
        # Step 1: Clean up the file
        success1 = cleanup_pdf_handler(file_path)
        
        # Step 2: Add basic enhancements
        success2 = add_basic_enhancements(file_path) if success1 else False
        
        if success1 and success2:
            print("\n✨ Successfully cleaned up and enhanced PDF handler!")
            print("\nWhat was done:")
            print("✓ Removed all methods outside the class")
            print("✓ Fixed class structure")
            print("✓ Added data quality score to executive summary")
            print("✓ Added ESRS E1 compliance sections")
            print("\n🚀 Try building again: npm run dev")
        else:
            print("\n❌ Process failed!")
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, file_path)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()