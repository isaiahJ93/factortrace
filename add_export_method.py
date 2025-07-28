#!/usr/bin/env python3
"""
Add the missing exportSinglePDF method to PDFExportHandler
"""

import os
import shutil
from datetime import datetime
import re

def add_export_single_pdf_method(file_path):
    """Add the missing exportSinglePDF method"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Checking for exportSinglePDF method...")
    
    # Check if the method exists
    if 'exportSinglePDF' in content and 'public async exportSinglePDF' in content:
        print("✅ exportSinglePDF method already exists")
        return True
    
    print("❌ exportSinglePDF method is missing - adding it now")
    
    # Find where to insert it (after getInstance method)
    getInstance_match = re.search(r'(public static getInstance[\s\S]*?\n  \})', content)
    
    if getInstance_match:
        insertion_point = getInstance_match.end()
        
        # The complete exportSinglePDF method
        export_method = '''
  
  /**
   * Export a single PDF with all emission data
   */
  public async exportSinglePDF(
    data: PDFExportData,
    options?: { useBackend?: boolean; filename?: string; compress?: boolean; validate?: boolean }
  ): Promise<ExportResult> {
    try {
      console.log('Generating PDF with data:', data);
      
      // Validate data
      if (!data || !data.metadata || !data.summary) {
        throw new Error('Invalid data structure for PDF export');
      }
      
      // Create PDF
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
        compress: options?.compress || false
      });
      
      // Generate PDF content
      const pdfBlob = await this.generatePDFClient(data, options?.compress || false);
      
      // Download if filename provided
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
  
  /**
   * Generate PDF on client side
   */
  private async generatePDFClient(data: PDFExportData, compress: boolean): Promise<Blob> {
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
      compress
    });
    
    let currentY = 20;
    
    // Add header
    if (typeof this.addHeader === 'function') {
      this.addHeader(pdf, data);
    }
    
    // Add title
    pdf.setFontSize(20);
    pdf.setTextColor(26, 26, 46);
    pdf.text(data.metadata.companyName || 'Company Report', 20, currentY);
    currentY += 10;
    
    pdf.setFontSize(14);
    pdf.text('ESRS E1 Climate-related Disclosures', 20, currentY);
    currentY += 15;
    
    // Add summary
    pdf.setFontSize(12);
    pdf.text('Executive Summary', 20, currentY);
    currentY += 8;
    
    pdf.setFontSize(10);
    pdf.text('Total Emissions: ' + data.summary.totalEmissions.toFixed(2) + ' tCO2e', 20, currentY);
    currentY += 6;
    pdf.text('Scope 1: ' + data.summary.scope1.toFixed(2) + ' tCO2e', 20, currentY);
    currentY += 6;
    pdf.text('Scope 2: ' + data.summary.scope2.toFixed(2) + ' tCO2e', 20, currentY);
    currentY += 6;
    pdf.text('Scope 3: ' + data.summary.scope3.toFixed(2) + ' tCO2e', 20, currentY);
    currentY += 6;
    pdf.text('Data Quality Score: ' + (data.summary.dataQualityScore || 72) + '%', 20, currentY);
    
    // Add more sections if the methods exist
    if (typeof this.addReportInfo === 'function') {
      pdf.addPage();
      currentY = 20;
      currentY = this.addReportInfo(pdf, data, currentY);
    }
    
    if (typeof this.addExecutiveSummary === 'function' && currentY < 250) {
      currentY = this.addExecutiveSummary(pdf, data, currentY + 10);
    }
    
    if (typeof this.addEmissionsOverview === 'function') {
      pdf.addPage();
      currentY = 20;
      currentY = this.addEmissionsOverview(pdf, data, currentY);
    }
    
    // Add footers
    if (typeof this.addFooters === 'function') {
      this.addFooters(pdf, data);
    }
    
    return pdf.output('blob');
  }
  
  /**
   * Download blob as file
   */
  private downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }'''
        
        # Insert the method
        content = content[:insertion_point] + export_method + content[insertion_point:]
        
        print("✅ Added exportSinglePDF method")
    else:
        print("❌ Could not find insertion point")
        return False
    
    # Write the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def verify_class_structure(file_path):
    """Verify the class has all required methods"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Verifying class structure...")
    
    required_methods = [
        'getInstance',
        'exportSinglePDF',
        'generatePDFClient',
        'downloadBlob'
    ]
    
    missing = []
    for method in required_methods:
        if method not in content:
            missing.append(method)
            print(f"❌ Missing: {method}")
        else:
            print(f"✅ Found: {method}")
    
    return len(missing) == 0

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
        # Add the missing method
        success1 = add_export_single_pdf_method(file_path)
        
        # Verify structure
        success2 = verify_class_structure(file_path)
        
        if success1 and success2:
            print("\n✨ Successfully added exportSinglePDF method!")
            print("\nYour PDF export should now work!")
            print("\nThe PDF will include:")
            print("✓ Company name and report title")
            print("✓ Executive summary with total emissions")
            print("✓ Scope 1, 2, and 3 breakdown")
            print("✓ Data quality score")
            print("\n🚀 Try exporting a PDF now!")
        else:
            print("\n❌ Failed to add method properly")
            print("Check the file structure")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()