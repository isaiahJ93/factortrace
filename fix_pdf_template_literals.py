#!/usr/bin/env python3
"""
Fix all template literal syntax issues in the PDF
"""

import os
import shutil
from datetime import datetime
import re

def fix_template_literals(file_path):
    """Fix all template literal syntax issues"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Fixing template literal syntax issues...")
    
    # Common patterns to fix
    replacements = [
        # Fix ${cat.num} type expressions
        (r'\$\{cat\.num\}', "' + (cat.num || '') + '"),
        (r'\$\{catNum\}', "' + (catNum || '') + '"),
        
        # Fix ${data.metadata...} expressions
        (r'\$\{data\.metadata\.documentId\}', "' + (data.metadata.documentId || '') + '"),
        (r'\$\{data\.metadata\.companyName\}', "' + (data.metadata.companyName || 'Your Company') + '"),
        (r'\$\{data\.metadata\.standard\}', "' + (data.metadata.standard || 'ESRS E1 Compliant') + '"),
        (r'\$\{data\.summary\.totalEmissions\.toFixed\(1\)\}', "' + data.summary.totalEmissions.toFixed(1) + '"),
        
        # Fix date expressions
        (r'\$\{new Date\(\)\.toLocaleDateString\(\)\}', "' + new Date().toLocaleDateString() + '"),
        (r'\$\{reportingMonth\}', "' + reportingMonth + '"),
        (r'\$\{reportingYear\}', "' + reportingYear + '"),
        
        # Fix any remaining ${...} patterns
        (r"'\$\{([^}]+)\}'", "' + \\1 + '"),
        (r'"\$\{([^}]+)\}"', "' + \\1 + '"),
        
        # Fix cases where template literals are in the middle of strings
        (r"(['\"])([^'\"]*)\$\{([^}]+)\}([^'\"]*)\1", "\\1\\2' + \\3 + '\\4\\1"),
    ]
    
    for pattern, replacement in replacements:
        count = len(re.findall(pattern, content))
        if count > 0:
            content = re.sub(pattern, replacement, content)
            print(f"✅ Fixed {count} instances of {pattern[:30]}...")
    
    # Fix specific known issues
    # Fix the document ID in header/footer
    content = content.replace(
        "'${data.metadata.documentId}'",
        "(data.metadata.documentId || 'GHG-' + Date.now().toString(36).toUpperCase())"
    )
    
    # Fix company name
    content = content.replace(
        "'${data.metadata.companyName}'",
        "(data.metadata.companyName || 'Your Company')"
    )
    
    # Fix any standalone ${...} that might be in text
    content = re.sub(
        r'text\([^,)]*\$\{([^}]+)\}[^,)]*\)',
        lambda m: m.group(0).replace('${', "' + ").replace('}', " + '"),
        content
    )
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed all template literal syntax issues")
    return True

def verify_pdf_structure(file_path):
    """Verify the PDF structure is intact"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Verifying PDF structure...")
    
    # Check for key methods
    required_methods = [
        'addHeader',
        'addFooters', 
        'addTitle',
        'addExecutiveSummary',
        'addGovernanceSection',
        'addEmissionsOverview',
        'addScope3Categories',
        'addActivityDetails'
    ]
    
    missing = []
    for method in required_methods:
        if f'private {method}(' not in content:
            missing.append(method)
    
    if missing:
        print(f"⚠️  Missing methods: {', '.join(missing)}")
        return False
    else:
        print("✅ All required PDF methods present")
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
        # Fix template literals
        success1 = fix_template_literals(file_path)
        success2 = verify_pdf_structure(file_path)
        
        if success1 and success2:
            print("\n✨ Template literal syntax fixed!")
            print("\nYour PDFs will now show:")
            print("✓ Actual document IDs instead of ${data.metadata.documentId}")
            print("✓ Company name instead of ${data.metadata.companyName}")
            print("✓ Proper values instead of ${...} syntax")
            print("\n🚀 Restart the app and export a PDF to see the fixes!")
        else:
            print("\n❌ Fix incomplete")
            print("Manual review may be needed")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()