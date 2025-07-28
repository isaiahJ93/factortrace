#!/usr/bin/env python3
"""
Check for common TypeScript issues in pdf-export-handler.ts
"""

import os
import re

def check_common_issues(file_path):
    """Check for common TypeScript issues"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Checking for common TypeScript issues...\n")
    
    issues_found = []
    
    # Check 1: DESIGN constant
    if 'const DESIGN' not in content and 'DESIGN =' not in content:
        issues_found.append("❌ DESIGN constant not found in file")
        print("❌ DESIGN constant is not defined in the file")
        print("   The ESRS methods use DESIGN.fonts, DESIGN.colors, DESIGN.layout")
        print("   This constant needs to be defined or imported\n")
    else:
        print("✅ DESIGN constant found\n")
    
    # Check 2: PDFExportData interface
    if 'interface PDFExportData' not in content:
        issues_found.append("❌ PDFExportData interface not found")
        print("❌ PDFExportData interface not defined")
    else:
        print("✅ PDFExportData interface found")
        
        # Check if it has the required properties
        interface_match = re.search(r'interface PDFExportData\s*\{([^}]+)\}', content, re.DOTALL)
        if interface_match:
            interface_content = interface_match.group(1)
            required_props = ['dataQuality', 'esrsE1Data', 'ghgBreakdown', 'uncertaintyAnalysis', 'results']
            
            for prop in required_props:
                if prop not in interface_content:
                    print(f"   ⚠️  Property '{prop}' not found in PDFExportData interface")
                    issues_found.append(f"Missing property: {prop}")
    
    print()
    
    # Check 3: Import statements
    print("📦 Checking imports...")
    if 'import jsPDF' not in content and 'from \'jspdf\'' not in content:
        issues_found.append("❌ jsPDF import missing")
        print("❌ jsPDF not imported")
    else:
        print("✅ jsPDF imported")
    
    print()
    
    # Check 4: Look for the actual syntax around line 1675
    lines = content.split('\n')
    if len(lines) > 1674:
        print("📍 Analyzing syntax around the error line...")
        
        # Get context
        start = max(0, 1670)
        end = min(len(lines), 1680)
        
        for i in range(start, end):
            if i < len(lines):
                line = lines[i]
                # Check for common syntax issues
                if i == 1674:  # Line before the error
                    if line.strip() and not line.strip().endswith(('*/', '{', '}', ';', ',')):
                        print(f"   ⚠️  Line {i+1} might be missing punctuation: {line.strip()}")
                
                # Check for invalid characters
                if i == 1674:  # The error line
                    if '\u200b' in line or '\u00a0' in line:
                        print(f"   ❌ Line {i+1} contains invisible/special characters!")
                        issues_found.append("Invisible characters in code")
    
    # Check 5: Spread operator usage
    spread_uses = re.findall(r'\.\.\.DESIGN\.(colors|fonts)\.\w+', content)
    if spread_uses:
        print(f"\n⚠️  Found {len(spread_uses)} uses of spread operator with DESIGN colors/fonts")
        print("   TypeScript might have issues with spreading color arrays")
        print("   Consider using explicit array syntax instead")
    
    # Summary
    print("\n" + "="*50)
    if issues_found:
        print(f"❌ Found {len(issues_found)} potential issues:")
        for issue in issues_found:
            print(f"   - {issue}")
    else:
        print("✅ No obvious issues found")
        print("\nThe error might be due to:")
        print("1. TypeScript version compatibility")
        print("2. tsconfig.json settings")
        print("3. Hidden characters in the file")
    
    return issues_found

def suggest_fixes(issues):
    """Suggest fixes for found issues"""
    
    print("\n🔧 Suggested fixes:\n")
    
    if any('DESIGN constant' in issue for issue in issues):
        print("1. Add DESIGN constant definition:")
        print("""
const DESIGN = {
  colors: {
    primary: [26, 26, 46] as [number, number, number],
    secondary: [100, 100, 100] as [number, number, number],
    text: [50, 50, 50] as [number, number, number],
    success: [16, 185, 129] as [number, number, number],
    warning: [245, 158, 11] as [number, number, number],
    error: [239, 68, 68] as [number, number, number]
  },
  fonts: {
    sizes: {
      title: 16,
      body: 11,
      small: 10
    }
  },
  layout: {
    margins: {
      left: 20,
      top: 20
    },
    pageHeight: 280
  }
};
""")
    
    if any('Property' in issue for issue in issues):
        print("\n2. Update PDFExportData interface to include missing properties")
        print("   Add optional properties like:")
        print("   dataQuality?: DataQualityMetrics;")
        print("   esrsE1Data?: any;")
        print("   ghgBreakdown?: any;")
        print("   uncertaintyAnalysis?: any;")
        print("   results?: any;")

def main():
    """Main function"""
    expected_dir = "/Users/isaiah/Documents/Scope3Tool"
    current_dir = os.getcwd()
    
    if current_dir != expected_dir:
        os.chdir(expected_dir)
    
    file_path = "./factortrace-frontend/src/components/emissions/pdf-export-handler.ts"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📁 Analyzing: {file_path}\n")
    
    issues = check_common_issues(file_path)
    
    if issues:
        suggest_fixes(issues)

if __name__ == "__main__":
    main()