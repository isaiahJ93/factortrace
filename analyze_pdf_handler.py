#!/usr/bin/env python3
"""
Examine the pdf-export-handler.ts file structure in detail
"""

import os
import re

def examine_pdf_handler_detailed(file_path):
    """Examine the pdf-export-handler.ts file in detail"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 Detailed File Analysis:\n")
    
    # Find the main generatePDFReport function
    pdf_report_match = re.search(r'((?:export\s+)?(?:async\s+)?function generatePDFReport[^{]*\{)([\s\S]*?)(\n\})', content)
    
    if pdf_report_match:
        print("✅ Found generatePDFReport function")
        function_body = pdf_report_match.group(2)
        
        # Extract key sections
        print("\n📑 Sections found in generatePDFReport:")
        
        # Look for section headers
        section_patterns = [
            (r'["\']Executive Summary["\']', 'Executive Summary'),
            (r'["\']Data Quality["\']', 'Data Quality'),
            (r'["\']ESRS E1["\']', 'ESRS E1'),
            (r'["\']Energy Consumption["\']', 'Energy Consumption'),
            (r'["\']Carbon Pricing["\']', 'Carbon Pricing'),
            (r'["\']Climate Actions["\']', 'Climate Actions'),
            (r'["\']GHG Breakdown["\']', 'GHG Breakdown'),
            (r'["\']Uncertainty Analysis["\']', 'Uncertainty Analysis'),
            (r'["\']Activity.*Breakdown["\']', 'Activity Breakdown'),
            (r'["\']Emissions by Scope["\']', 'Emissions by Scope'),
            (r'["\']Top.*Categories["\']', 'Top Categories'),
        ]
        
        found_sections = []
        for pattern, name in section_patterns:
            if re.search(pattern, function_body, re.IGNORECASE):
                found_sections.append(name)
                print(f"  ✓ {name}")
        
        missing_sections = []
        required_sections = [
            'Data Quality', 'Energy Consumption', 'Carbon Pricing', 
            'Climate Actions', 'GHG Breakdown', 'Uncertainty Analysis',
            'Emissions by Scope', 'Top Categories'
        ]
        
        for section in required_sections:
            if section not in found_sections:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"\n❌ Missing sections: {', '.join(missing_sections)}")
        
        # Show a snippet of the function structure
        print("\n📄 Function structure preview:")
        lines = function_body.split('\n')[:50]  # First 50 lines
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['Executive Summary', 'Data Quality', 'ESRS E1', 'doc.text', 'doc.addPage']):
                print(f"  Line {i}: {line.strip()[:80]}...")
    
    # Check if it's using a different structure (like class methods)
    class_match = re.search(r'class PDFExportHandler[^{]*\{([\s\S]*?)\n\}', content)
    if class_match:
        print("\n✅ Found PDFExportHandler class")
        class_body = class_match.group(1)
        
        # Find methods in the class
        methods = re.findall(r'(?:private\s+|public\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)\s*[:{]', class_body)
        if methods:
            print(f"  Methods: {', '.join(methods[:10])}")
    
    # Look for where content is actually being added
    print("\n🔍 Content generation patterns found:")
    
    patterns = [
        (r'doc\.text\([^,]+,\s*[^,]+,\s*[^)]+\)', 'doc.text calls'),
        (r'doc\.autoTable\(', 'autoTable calls'),
        (r'doc\.addPage\(', 'addPage calls'),
        (r'generateSection|addSection|createSection', 'section generation methods'),
    ]
    
    for pattern, description in patterns:
        matches = re.findall(pattern, content)
        if matches:
            print(f"  ✓ {description}: {len(matches)} occurrences")
            # Show first few examples
            for match in matches[:3]:
                print(f"    - {match[:60]}...")
    
    return content, found_sections, missing_sections

def suggest_update_strategy(content, missing_sections):
    """Suggest the best update strategy based on file structure"""
    
    print("\n💡 Update Strategy Recommendation:\n")
    
    if 'class PDFExportHandler' in content:
        if 'generateSections' in content or 'addSection' in content:
            print("This file uses a class-based approach with section methods.")
            print("Recommendation: Add new methods for missing sections.")
        else:
            print("This file uses a class-based approach.")
            print("Recommendation: Extend the main generation method.")
    elif 'generatePDFReport' in content:
        if 'doc.autoTable' in content:
            print("This file uses autoTable for content generation.")
            print("Recommendation: Add new sections after existing tables.")
        else:
            print("This file uses direct doc.text() calls.")
            print("Recommendation: Insert new sections in the main function.")
    
    if missing_sections:
        print(f"\nNeed to add: {', '.join(missing_sections)}")

def create_targeted_update(file_path, missing_sections):
    """Create a targeted update based on what's missing"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔧 Creating targeted update...\n")
    
    # Save current state
    with open(f"{file_path}.analysis.txt", 'w') as f:
        f.write(f"PDF Export Handler Analysis\n")
        f.write(f"==========================\n\n")
        f.write(f"Missing sections: {', '.join(missing_sections)}\n\n")
        f.write(f"File structure:\n")
        f.write(content[:2000])
        f.write("\n... (truncated)")
    
    print(f"✅ Analysis saved to: {file_path}.analysis.txt")
    print("\nPlease share the analysis file so I can create a precise update.")

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
    
    print(f"📁 Analyzing: {file_path}")
    
    content, found_sections, missing_sections = examine_pdf_handler_detailed(file_path)
    suggest_update_strategy(content, missing_sections)
    
    if missing_sections:
        create_targeted_update(file_path, missing_sections)
        print("\n📋 Next steps:")
        print("1. Review the analysis file")
        print("2. Share any relevant code snippets")
        print("3. I'll create a precise update script")
    else:
        print("\n✅ All required sections appear to be present!")
        print("The PDF export handler may already include the necessary ESRS E1 content.")

if __name__ == "__main__":
    main()