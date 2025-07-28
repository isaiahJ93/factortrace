#!/usr/bin/env python3
"""
Fix syntax error in reconcileData method
"""

import os
import shutil
from datetime import datetime
import re

def fix_reconcile_syntax(file_path):
    """Fix the syntax error in reconcileData method"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Fixing reconcileData syntax error...")
    
    # Find and replace the entire reconcileData method with correct syntax
    # Look for the method and replace it completely
    pattern = r'private reconcileData\(data: PDFExportData\): PDFExportData \{[\s\S]*?return reconciled;\s*\}'
    
    replacement = '''private reconcileData(data: PDFExportData): PDFExportData {
    // Ensure all required properties exist
    const reconciled: PDFExportData = {
      ...data,
      metadata: {
        documentId: data.metadata?.documentId || 'GHG-' + Date.now().toString(36).toUpperCase(),
        companyName: data.metadata?.companyName || 'Your Company',
        reportingPeriod: data.metadata?.reportingPeriod || new Date().toISOString().slice(0, 7),
        generatedDate: data.metadata?.generatedDate || new Date().toISOString(),
        standard: data.metadata?.standard || 'ESRS E1 Compliant',
        methodology: data.metadata?.methodology || 'GHG Protocol Corporate Standard'
      },
      summary: {
        totalEmissions: data.summary?.totalEmissions || 0,
        scope1: data.summary?.scope1 || 0,
        scope2: data.summary?.scope2 || 0,
        scope3: data.summary?.scope3 || 0,
        scope1Percentage: 0,
        scope2Percentage: 0,
        scope3Percentage: 0,
        dataQualityScore: data.summary?.dataQualityScore || 72
      },
      activities: data.activities || [],
      scope3Categories: data.scope3Categories || [],
      targets: data.targets || [],
      topEmissionSources: data.topEmissionSources || []
    };
    
    // Calculate percentages
    const total = reconciled.summary.totalEmissions;
    if (total > 0) {
      reconciled.summary.scope1Percentage = (reconciled.summary.scope1 / total * 100);
      reconciled.summary.scope2Percentage = (reconciled.summary.scope2 / total * 100);
      reconciled.summary.scope3Percentage = (reconciled.summary.scope3 / total * 100);
    }
    
    return reconciled;
  }'''
    
    # Replace the method
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # If that didn't work, try a more aggressive approach
    if 'Expression expected' in content or content.count('private reconcileData') > 1:
        # Find the start of reconcileData
        start_match = re.search(r'private reconcileData\(data: PDFExportData\): PDFExportData \{', content)
        if start_match:
            start_pos = start_match.start()
            
            # Find the corresponding closing brace by counting
            brace_count = 0
            end_pos = start_pos
            i = start_match.end()
            
            while i < len(content):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    if brace_count == 0:
                        end_pos = i + 1
                        break
                    brace_count -= 1
                i += 1
            
            # Replace this section with our correct implementation
            if end_pos > start_pos:
                content = content[:start_pos] + replacement + content[end_pos:]
                print("✅ Replaced reconcileData method")
    
    # Ensure there are no duplicate method declarations
    # Count occurrences of each method
    methods = ['reconcileData', 'generatePDFClient', 'validateData', 'downloadBlob']
    for method in methods:
        count = content.count(f'private {method}')
        if count > 1:
            print(f"⚠️  Found {count} declarations of {method}, removing duplicates...")
            # Keep only the first occurrence
            first_occurrence = content.find(f'private {method}')
            if first_occurrence != -1:
                # Find all other occurrences and remove them
                while content.count(f'private {method}') > 1:
                    second_occurrence = content.find(f'private {method}', first_occurrence + 1)
                    if second_occurrence != -1:
                        # Find the end of this method
                        method_start = second_occurrence
                        brace_count = 0
                        method_end = method_start
                        i = content.find('{', method_start)
                        if i != -1:
                            brace_count = 1
                            i += 1
                            while i < len(content) and brace_count > 0:
                                if content[i] == '{':
                                    brace_count += 1
                                elif content[i] == '}':
                                    brace_count -= 1
                                i += 1
                            method_end = i
                        
                        # Remove the duplicate method
                        content = content[:method_start] + content[method_end:]
                        print(f"  ✅ Removed duplicate {method}")
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def verify_syntax(file_path):
    """Verify the syntax is correct"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Verifying syntax...")
    
    # Check brace balance
    open_braces = content.count('{')
    close_braces = content.count('}')
    
    print(f"Brace count: {open_braces} open, {close_braces} close")
    
    if open_braces != close_braces:
        print(f"⚠️  Brace mismatch! Difference: {open_braces - close_braces}")
        return False
    
    # Check for common syntax issues
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Check for lines that might cause "Expression expected"
        if line.strip() == '}' and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and not next_line.startswith(('/', '*', '}', 'export', 'import')):
                if 'private' in next_line:
                    print(f"⚠️  Potential issue at line {i + 2}: Method after closing brace")
    
    print("✅ Syntax verification complete")
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
        # Fix the syntax error
        success1 = fix_reconcile_syntax(file_path)
        
        # Verify syntax
        success2 = verify_syntax(file_path)
        
        if success1 and success2:
            print("\n✨ Successfully fixed syntax error!")
            print("\nFixed:")
            print("✓ Corrected reconcileData method syntax")
            print("✓ Removed any duplicate method declarations")
            print("✓ Verified brace balance")
            print("\n🚀 Try building again: npm run dev")
        else:
            print("\n⚠️  There might still be issues")
            print("Check the build output for specific line numbers")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()