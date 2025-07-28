#!/usr/bin/env python3
"""
Fix the context around the interface declaration
"""

import os
import shutil
from datetime import datetime

def fix_interface_context(file_path):
    """Fix the context around the interface declaration"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Analyzing context around line 35...")
    
    # Show context
    start = max(0, 30)
    end = min(len(lines), 40)
    
    print("\nContext:")
    for i in range(start, end):
        marker = ">>>" if i == 34 else "   "
        print(f"{marker} {i + 1:3d}: {lines[i].rstrip()}")
    
    # Look for issues before line 35
    if len(lines) > 34:
        # Check what's on line 34 (index 33)
        line_34 = lines[33].strip()
        line_35 = lines[34].strip() if len(lines) > 34 else ""
        
        print(f"\nLine 34: '{line_34}'")
        print(f"Line 35: '{line_35}'")
        
        # Common issues:
        # 1. Missing closing brace from previous structure
        # 2. Missing semicolon
        # 3. Extra characters
        
        # If line 34 has incomplete syntax
        if line_34 and not line_34.endswith((';', '}', '{', '*/')) and line_34 != '':
            print("⚠️  Line 34 might be missing punctuation")
            
            # If it's just a closing brace, make sure it's proper
            if line_34 == '}':
                lines[33] = '}\n'
            elif 'const' in line_34 or 'let' in line_34 or 'var' in line_34:
                lines[33] = line_34 + ';\n'
        
        # Check if there's something between a closing brace and the interface
        if len(lines) > 33:
            # Look backwards for any unclosed structures
            brace_count = 0
            for i in range(33, -1, -1):
                brace_count += lines[i].count('{')
                brace_count -= lines[i].count('}')
            
            if brace_count > 0:
                print(f"⚠️  Found {brace_count} unclosed braces before interface")
                # Add closing braces before the interface
                lines.insert(34, '};\n' * brace_count)
    
    # Ensure clean interface declaration
    interface_line = None
    for i, line in enumerate(lines):
        if 'export interface PDFExportData' in line:
            interface_line = i
            break
    
    if interface_line is not None:
        # Make sure there's a blank line before the interface
        if interface_line > 0 and lines[interface_line - 1].strip() != '':
            lines.insert(interface_line, '\n')
            interface_line += 1
        
        # Fix the interface declaration
        lines[interface_line] = 'export interface PDFExportData {\n'
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return True

def rebuild_top_section(file_path):
    """Rebuild the top section of the file with correct structure"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔧 Rebuilding file structure...")
    
    # Extract the class and everything after the interfaces
    class_start = content.find('export class PDFExportHandler')
    if class_start == -1:
        print("❌ Could not find class")
        return False
    
    class_and_after = content[class_start:]
    
    # Build a clean top section
    clean_top = '''import jsPDF from 'jspdf';
import 'jspdf-autotable';

// Design constants
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
      subtitle: 14,
      body: 11,
      small: 10,
      tiny: 9
    }
  },
  layout: {
    margins: {
      top: 20,
      bottom: 20,
      left: 20,
      right: 20
    },
    pageHeight: 297,
    pageWidth: 210
  }
};

export interface PDFExportData {
  metadata: {
    documentId?: string;
    companyName: string;
    reportingPeriod: string;
    generatedDate: string;
    standard?: string;
    methodology?: string;
  };
  summary: {
    totalEmissions: number;
    scope1: number;
    scope2: number;
    scope3: number;
    scope1Percentage?: number;
    scope2Percentage?: number;
    scope3Percentage?: number;
    dataQualityScore?: number;
  };
  governance?: any;
  targets?: any[];
  activities?: any[];
  scope3Categories?: any[];
  topEmissionSources?: any[];
  [key: string]: any;
}

export interface ExportResult {
  success: boolean;
  blob: Blob | null;
  error?: string;
}

/**
 * PDF Export Handler for ESRS E1 compliant reports
 */
'''
    
    # Combine clean top with the rest
    new_content = clean_top + class_and_after
    
    # Write the new content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Rebuilt file structure")
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
        # First try to fix the context
        success1 = fix_interface_context(file_path)
        
        if not success1:
            print("\n⚠️  Context fix didn't work, rebuilding file structure...")
            # If that doesn't work, rebuild the top section
            success2 = rebuild_top_section(file_path)
            
            if success2:
                print("\n✨ Successfully rebuilt file structure!")
            else:
                print("\n❌ Rebuild failed")
                print(f"Restoring from backup: {backup_path}")
                shutil.copy2(backup_path, file_path)
        else:
            print("\n✨ Successfully fixed interface context!")
        
        print("\n🚀 Try building again: npm run dev")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()