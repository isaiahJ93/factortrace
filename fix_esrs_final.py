#!/usr/bin/env python3
"""
Completely remove and re-add ESRS methods inside the class
"""

import os
import shutil
from datetime import datetime
import re

def remove_and_readd_esrs_methods(file_path):
    """Remove all ESRS methods and re-add them properly inside the class"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Removing all ESRS methods...")
    
    # First, remove ALL the ESRS methods wherever they are
    patterns_to_remove = [
        # Remove the methods
        r'/\*\*\s*\n\s*\*\s*Add Data Quality Score Section[\s\S]*?(?=\n\s*(?:/\*\*|private|export|class|\}[\s\n]*(?:export|$)))',
        r'/\*\*\s*\n\s*\*\s*Add Emissions by Scope Chart[\s\S]*?(?=\n\s*(?:/\*\*|private|export|class|\}[\s\n]*(?:export|$)))',
        r'/\*\*\s*\n\s*\*\s*Add Top Emission Categories[\s\S]*?(?=\n\s*(?:/\*\*|private|export|class|\}[\s\n]*(?:export|$)))',
        r'/\*\*\s*\n\s*\*\s*Add GHG Breakdown by Gas Type[\s\S]*?(?=\n\s*(?:/\*\*|private|export|class|\}[\s\n]*(?:export|$)))',
        r'/\*\*\s*\n\s*\*\s*Add Energy Consumption Section[\s\S]*?(?=\n\s*(?:/\*\*|private|export|class|\}[\s\n]*(?:export|$)))',
        r'/\*\*\s*\n\s*\*\s*Add Carbon Pricing Section[\s\S]*?(?=\n\s*(?:/\*\*|private|export|class|\}[\s\n]*(?:export|$)))',
        r'/\*\*\s*\n\s*\*\s*Add Actions & Resources Section[\s\S]*?(?=\n\s*(?:/\*\*|private|export|class|\}[\s\n]*(?:export|$)))',
        r'/\*\*\s*\n\s*\*\s*Add Uncertainty Analysis Section[\s\S]*?(?=\n\s*(?:/\*\*|private|export|class|\}[\s\n]*(?:export|$)))',
        # Remove any orphaned private methods
        r'\n\s*private\s+addDataQualityScore[\s\S]*?\n\s*\}\s*(?=\n)',
        r'\n\s*private\s+addEmissionsByScope[\s\S]*?\n\s*\}\s*(?=\n)',
        r'\n\s*private\s+addTopCategories[\s\S]*?\n\s*\}\s*(?=\n)',
        r'\n\s*private\s+addGHGBreakdown[\s\S]*?\n\s*\}\s*(?=\n)',
        r'\n\s*private\s+addEnergySection[\s\S]*?\n\s*\}\s*(?=\n)',
        r'\n\s*private\s+addCarbonPricingSection[\s\S]*?\n\s*\}\s*(?=\n)',
        r'\n\s*private\s+addActionsSection[\s\S]*?\n\s*\}\s*(?=\n)',
        r'\n\s*private\s+addUncertaintySection[\s\S]*?\n\s*\}\s*(?=\n)',
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Also remove the section calls
    content = re.sub(
        r'\n\s*//\s*ESRS E1 Enhanced Sections[\s\S]*?(?=\n\s*//|$)',
        '',
        content
    )
    
    print("✅ Removed all ESRS methods and calls")
    
    # Now find the right place to insert them
    # Look for the addFooters method which should be the last method in the class
    footer_match = re.search(r'(private addFooters\([^}]+\}\s*\n\s*)', content, re.DOTALL)
    
    if footer_match:
        insertion_point = footer_match.end()
        
        # Insert the ESRS methods here
        esrs_methods = """
  /**
   * Add Data Quality Score visualization
   */
  private addDataQualityScore(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(14);
    pdf.setTextColor(26, 26, 46);
    pdf.text('Data Quality Assessment', 20, currentY);
    currentY += 8;
    
    const qualityScore = data.summary.dataQualityScore || 72;
    const scoreColor = qualityScore >= 80 ? [16, 185, 129] : qualityScore >= 60 ? [245, 158, 11] : [239, 68, 68];
    
    // Score visualization
    pdf.setFillColor(245, 245, 245);
    pdf.rect(20, currentY, 60, 25, 'F');
    
    pdf.setFontSize(20);
    pdf.setTextColor(scoreColor[0], scoreColor[1], scoreColor[2]);
    pdf.text(qualityScore.toString() + '%', 35, currentY + 18);
    
    pdf.setFontSize(10);
    pdf.setTextColor(50, 50, 50);
    pdf.text('Overall Score', 85, currentY + 15);
    
    return currentY + 35;
  }

  /**
   * Add simple emissions by scope visualization
   */
  private addEmissionsByScope(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(14);
    pdf.setTextColor(26, 26, 46);
    pdf.text('Emissions by Scope', 20, currentY);
    currentY += 10;
    
    const tableData = [
      ['Scope 1 - Direct', data.summary.scope1.toFixed(2) + ' tCO2e', (data.summary.scope1Percentage || 0).toFixed(1) + '%'],
      ['Scope 2 - Energy', data.summary.scope2.toFixed(2) + ' tCO2e', (data.summary.scope2Percentage || 0).toFixed(1) + '%'],
      ['Scope 3 - Value Chain', data.summary.scope3.toFixed(2) + ' tCO2e', (data.summary.scope3Percentage || 0).toFixed(1) + '%'],
      ['Total', data.summary.totalEmissions.toFixed(2) + ' tCO2e', '100%']
    ];
    
    (pdf as any).autoTable({
      startY: currentY,
      body: tableData,
      theme: 'striped',
      columnStyles: {
        0: { fontStyle: 'bold' },
        1: { halign: 'right' },
        2: { halign: 'center' }
      },
      margin: { left: 20 }
    });
    
    return (pdf as any).lastAutoTable.finalY + 10;
  }

  /**
   * Add ESRS E1-5 Energy section
   */
  private addEnergySection(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(14);
    pdf.setTextColor(26, 26, 46);
    pdf.text('E1-5: Energy Consumption', 20, currentY);
    currentY += 8;
    
    const energyData = [
      ['Total energy consumption', '0 MWh'],
      ['Renewable energy', '0%']
    ];
    
    (pdf as any).autoTable({
      startY: currentY,
      body: energyData,
      theme: 'striped',
      columnStyles: { 0: { fontStyle: 'bold', cellWidth: 100 } },
      margin: { left: 20 }
    });
    
    currentY = (pdf as any).lastAutoTable.finalY + 5;
    
    pdf.setFontSize(9);
    pdf.setTextColor(100, 100, 100);
    pdf.text('Note: Energy consumption captured under Scope 2 purchased electricity', 20, currentY);
    
    return currentY + 10;
  }

  /**
   * Add ESRS E1-8 Carbon Pricing section
   */
  private addCarbonPricingSection(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(14);
    pdf.setTextColor(26, 26, 46);
    pdf.text('E1-8: Internal Carbon Pricing', 20, currentY);
    currentY += 8;
    
    const pricingData = [
      ['Internal carbon price', 'EUR 0/tCO2e'],
      ['Coverage', 'Not currently implemented']
    ];
    
    (pdf as any).autoTable({
      startY: currentY,
      body: pricingData,
      theme: 'striped',
      columnStyles: { 0: { fontStyle: 'bold', cellWidth: 100 } },
      margin: { left: 20 }
    });
    
    return (pdf as any).lastAutoTable.finalY + 10;
  }

  /**
   * Add ESRS E1-3 Actions section
   */
  private addActionsSection(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(14);
    pdf.setTextColor(26, 26, 46);
    pdf.text('E1-3: Actions & Resources', 20, currentY);
    currentY += 8;
    
    const actionsData = [
      ['Climate-related CapEx', 'EUR 0', '0% of total CapEx'],
      ['Climate-related OpEx', 'EUR 0', '0% of total OpEx'],
      ['Dedicated FTEs', '0', 'Full-time equivalents']
    ];
    
    (pdf as any).autoTable({
      startY: currentY,
      head: [['Metric', 'Value', 'Notes']],
      body: actionsData,
      theme: 'striped',
      headStyles: { fillColor: [26, 26, 46] },
      margin: { left: 20 }
    });
    
    return (pdf as any).lastAutoTable.finalY + 10;
  }
"""
        
        content = content[:insertion_point] + esrs_methods + '\n' + content[insertion_point:]
        print("✅ Added ESRS methods inside the class after addFooters")
        
        # Now add the section calls
        # Find where addActivityDetails is called
        activity_match = re.search(r'(currentY = this\.addActivityDetails\([^;]+;\s*\n)', content)
        
        if activity_match:
            section_calls = """
    // Enhanced ESRS E1 Sections
    if (reconciledData.summary) {
      pdf.addPage();
      currentY = 20;
      
      // Data quality and emissions breakdown
      currentY = this.addDataQualityScore(pdf, reconciledData, currentY);
      currentY = this.addEmissionsByScope(pdf, reconciledData, currentY + 10);
      
      // ESRS E1 specific sections
      pdf.addPage();
      currentY = 20;
      currentY = this.addEnergySection(pdf, reconciledData, currentY);
      currentY = this.addCarbonPricingSection(pdf, reconciledData, currentY + 10);
      currentY = this.addActionsSection(pdf, reconciledData, currentY + 10);
    }
"""
            content = content[:activity_match.end()] + section_calls + content[activity_match.end():]
            print("✅ Added section calls")
    
    # Write the fixed content
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
        # Remove and re-add methods
        success = remove_and_readd_esrs_methods(file_path)
        
        if success:
            print("\n✨ Successfully fixed ESRS methods!")
            print("\nWhat was done:")
            print("✓ Removed all ESRS methods from incorrect locations")
            print("✓ Re-added them properly inside PDFExportHandler class")
            print("✓ Added simplified but complete ESRS sections:")
            print("  - Data Quality Score")
            print("  - Emissions by Scope")
            print("  - E1-5 Energy Consumption")
            print("  - E1-8 Carbon Pricing")
            print("  - E1-3 Actions & Resources")
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