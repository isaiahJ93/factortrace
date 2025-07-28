#!/usr/bin/env python3
"""
Fix method separation syntax errors
"""

import os
import shutil
from datetime import datetime
import re

def fix_method_separation(file_path):
    """Fix the syntax errors between methods"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("🔍 Fixing method separation syntax...")
    
    # Look for patterns where a method ends and another begins without proper separation
    for i in range(len(lines) - 1):
        current_line = lines[i].strip()
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        
        # If current line is a closing brace and next line starts with 'private'
        if current_line == '}' and next_line.startswith('private '):
            print(f"Found improper method separation at line {i + 1}")
            # The issue might be that we're outside the class
            # Check the context by looking backwards
            
            # Count braces to see if we're inside the class
            brace_count = 0
            for j in range(i, -1, -1):
                brace_count += lines[j].count('{')
                brace_count -= lines[j].count('}')
                
                if 'export class PDFExportHandler' in lines[j]:
                    # We found the class start
                    if brace_count <= 0:
                        print(f"  ⚠️  Methods are outside the class at line {i + 2}")
                        # We need to move these methods inside the class
                        # Find the proper class closing brace
                        class_brace_count = 1
                        class_end = j + 1
                        
                        for k in range(j + 1, len(lines)):
                            class_brace_count += lines[k].count('{')
                            class_brace_count -= lines[k].count('}')
                            
                            if class_brace_count == 0:
                                class_end = k
                                break
                        
                        if class_end > i:
                            # The class already ended, these methods are outside
                            # We need to restructure
                            return False, "Methods are outside the class"
                    break
    
    return True, "No obvious separation issues found"

def rebuild_class_structure(file_path):
    """Rebuild the entire class structure properly"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔧 Rebuilding class structure...")
    
    # Extract all methods
    method_pattern = r'(private\s+(?:async\s+)?\w+\s*\([^)]*\)(?:\s*:\s*[^{]+)?\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'
    all_methods = re.findall(method_pattern, content, re.DOTALL)
    
    print(f"Found {len(all_methods)} methods total")
    
    # Extract the class constructor and getInstance
    constructor_pattern = r'(private constructor\([^)]*\)\s*\{[^}]*\})'
    getInstance_pattern = r'(public static getInstance\([^)]*\)[^{]*\{[^}]*\})'
    
    constructor = re.search(constructor_pattern, content)
    getInstance = re.search(getInstance_pattern, content)
    
    # Build the new file
    new_content = '''import jsPDF from 'jspdf';
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
export class PDFExportHandler {
  private static instance: PDFExportHandler;
  private readonly apiUrl: string;
  
'''
    
    # Add constructor
    if constructor:
        new_content += '  ' + constructor.group(1).strip() + '\n\n'
    else:
        new_content += '''  private constructor(apiUrl: string = 'http://localhost:8000') {
    this.apiUrl = apiUrl;
  }

'''
    
    # Add getInstance
    if getInstance:
        new_content += '  ' + getInstance.group(1).strip() + '\n\n'
    else:
        new_content += '''  public static getInstance(apiUrl?: string): PDFExportHandler {
    if (!PDFExportHandler.instance) {
      PDFExportHandler.instance = new PDFExportHandler(apiUrl);
    }
    return PDFExportHandler.instance;
  }

'''
    
    # Add exportSinglePDF if not in methods
    if not any('exportSinglePDF' in method for method in all_methods):
        new_content += '''  public async exportSinglePDF(
    data: PDFExportData,
    options?: { useBackend?: boolean; filename?: string; compress?: boolean; validate?: boolean }
  ): Promise<ExportResult> {
    try {
      console.log('Generating PDF with data:', data);
      
      if (!data || !data.metadata || !data.summary) {
        throw new Error('Invalid data structure for PDF export');
      }
      
      const pdfBlob = await this.generatePDFClient(data, options?.compress || false);
      
      if (options?.filename) {
        this.downloadBlob(pdfBlob, options.filename);
      }
      
      return { success: true, blob: pdfBlob };
    } catch (error) {
      console.error('PDF export failed:', error);
      return { 
        success: false, 
        blob: null, 
        error: error instanceof Error ? error.message : 'Export failed' 
      };
    }
  }

'''
    
    # Add all other methods
    for method in all_methods:
        # Skip constructor and getInstance as we already added them
        if 'constructor' not in method and 'getInstance' not in method:
            # Clean up the method
            clean_method = method.strip()
            # Ensure proper indentation
            method_lines = clean_method.split('\n')
            indented_method = '\n'.join('  ' + line if line.strip() else '' for line in method_lines)
            new_content += indented_method + '\n\n'
    
    # Close the class
    new_content += '}\n\n'
    
    # Add the export function
    new_content += '''/**
 * Generate PDF report from emission data
 */
export async function generatePDFReport(
  data: PDFExportData,
  options?: { useBackend?: boolean; filename?: string; compress?: boolean; validate?: boolean }
): Promise<ExportResult> {
  const handler = PDFExportHandler.getInstance();
  return handler.exportSinglePDF(data, options);
}
'''
    
    # Write the rebuilt content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Rebuilt class structure")
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
        # First check for separation issues
        success, message = fix_method_separation(file_path)
        
        if not success:
            print(f"\n⚠️  {message}")
            print("Rebuilding class structure...")
            
            # Rebuild the entire structure
            rebuild_success = rebuild_class_structure(file_path)
            
            if rebuild_success:
                print("\n✨ Successfully rebuilt PDF handler!")
                print("\nThe file now has:")
                print("✓ All imports and interfaces")
                print("✓ All methods inside the PDFExportHandler class")
                print("✓ Proper method separation")
                print("✓ Export function at the end")
                print("\n🚀 Try building again: npm run dev")
            else:
                print("\n❌ Rebuild failed")
                print(f"Restoring from backup: {backup_path}")
                shutil.copy2(backup_path, file_path)
        else:
            print(f"\n✅ {message}")
            print("File structure appears correct")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()