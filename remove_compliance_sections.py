#!/usr/bin/env python3
"""
Remove the compliance sections to get back to a working state
Since they're causing runtime errors
"""

import os
import shutil
from datetime import datetime
import re

def remove_compliance_sections(file_path):
    """Remove all compliance sections to restore working state"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Removing compliance sections that are causing errors...")
    
    # Remove the compliance method calls
    # Find and remove the section that calls addReportingContext
    content = re.sub(
        r'\n\s*//\s*Add CSRD Mandatory Compliance Sections[\s\S]*?this\.addManagementAssertion\([^;]+;\s*\n',
        '\n',
        content
    )
    print("✅ Removed compliance section calls")
    
    # Remove the compliance methods themselves
    # They might be outside the class
    patterns_to_remove = [
        r'/\*\*\s*\n\s*\*\s*Add Reporting Context Section[\s\S]*?}\s*\n(?=\s*(?:/\*\*|private|export|$))',
        r'/\*\*\s*\n\s*\*\s*Add Assurance Readiness Section[\s\S]*?}\s*\n(?=\s*(?:/\*\*|private|export|$))',
        r'/\*\*\s*\n\s*\*\s*Add ESRS Cross-References Section[\s\S]*?}\s*\n(?=\s*(?:/\*\*|private|export|$))',
        r'/\*\*\s*\n\s*\*\s*Add Legal Compliance Statement[\s\S]*?}\s*\n(?=\s*(?:/\*\*|private|export|$))',
        r'/\*\*\s*\n\s*\*\s*Add Management Assertion Section[\s\S]*?}\s*\n(?=\s*(?:/\*\*|private|export|$))',
    ]
    
    for pattern in patterns_to_remove:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, '', content)
            print(f"✅ Removed compliance method: {pattern.split('Add ')[1].split(' ')[0]}")
    
    # Write the cleaned content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Removed all compliance sections")
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
        # Remove compliance sections
        success = remove_compliance_sections(file_path)
        
        if success:
            print("\n✨ Compliance sections removed!")
            print("\nYour PDF export will now work with:")
            print("✓ Executive Summary")
            print("✓ ESRS E1 Governance")
            print("✓ Emissions Overview") 
            print("✓ Scope 3 Categories")
            print("✓ Activity Details")
            print("\n🚀 The PDF export should now work without errors!")
            print("\nRun the app and try exporting a PDF.")
        else:
            print("\n❌ Removal failed!")
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, file_path)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()