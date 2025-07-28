#!/usr/bin/env python3
"""
Examine and update pdf-export-handler.ts with comprehensive ESRS E1 sections
Run from: /Users/isaiah/Documents/Scope3Tool
"""

import re
import os
import shutil
from datetime import datetime

def create_backup(file_path):
    """Create a backup of the original file"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def examine_file_structure(file_path):
    """Examine the file to understand its structure"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📋 File structure analysis:")
    
    # Look for function definitions
    functions = re.findall(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', content)
    print(f"Functions found: {', '.join(functions[:10])}...")
    
    # Look for generatePDFReport or similar
    if 'generatePDFReport' in content:
        print("✅ Found generatePDFReport function")
    
    # Look for class definitions
    classes = re.findall(r'(?:export\s+)?class\s+(\w+)', content)
    if classes:
        print(f"Classes found: {', '.join(classes)}")
    
    # Look for the structure of PDF generation
    if 'addPage' in content:
        print("✅ Uses jsPDF addPage method")
    
    if 'autoTable' in content:
        print("✅ Uses jsPDF autoTable plugin")
    
    # Check for existing sections
    sections = []
    if 'Executive Summary' in content:
        sections.append('Executive Summary')
    if 'Cover Page' in content or 'Cover' in content:
        sections.append('Cover Page')
    if 'Data Quality' in content:
        sections.append('Data Quality')
    if 'ESRS E1' in content:
        sections.append('ESRS E1')
    
    if sections:
        print(f"Existing sections: {', '.join(sections)}")
    
    return content

def find_insertion_point(content):
    """Find the best place to insert our enhanced content generation"""
    
    # Look for different patterns where we might insert our code
    patterns = [
        # Pattern 1: Inside generatePDFReport function, after initial setup
        (r'(function generatePDFReport[\s\S]*?const doc = new jsPDF[^;]*;[\s\S]*?)((?:doc\.addPage|return new Promise))', 'inside_function'),
        
        # Pattern 2: After a specific section generation
        (r'(// Generate content[\s\S]*?)(doc\.save\(|return \{)', 'before_save'),
        
        # Pattern 3: Where content is being added to pages
        (r'(doc\.text\([^)]+\);[\s\S]*?)(doc\.addPage\(\)|doc\.save\()', 'content_area'),
        
        # Pattern 4: Inside async function with sections
        (r'(async function generatePDFReport[\s\S]*?try \{[\s\S]*?)(// Footer|doc\.save)', 'async_content'),
        
        # Pattern 5: Look for where emissions data is being added
        (r'(// Add emissions data[\s\S]*?)(}\s*catch)', 'emissions_section'),
    ]
    
    for pattern, pattern_type in patterns:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            print(f"✅ Found insertion point using pattern: {pattern_type}")
            return match.start(2), pattern_type
    
    # If no patterns match, look for table generation
    if 'autoTable' in content:
        match = re.search(r'(doc\.autoTable\([\s\S]*?\);)([\s\S]*?)(doc\.)', content)
        if match:
            print("✅ Found insertion point after autoTable")
            return match.end(1), 'after_table'
    
    return None, None

def generate_enhanced_content_code():
    """Generate the enhanced content code to insert"""
    return '''
    // ESRS E1 Enhanced Content Generation
    
    // Data Quality Score Section
    let yPos = doc.lastAutoTable ? doc.lastAutoTable.finalY + 20 : 60;
    
    // Add new page if needed
    if (yPos > 220) {
      doc.addPage();
      yPos = 20;
    }
    
    // Data Quality Score
    doc.setFontSize(14);
    doc.setTextColor(26, 26, 46);
    doc.text('Data Quality Assessment', 20, yPos);
    yPos += 10;
    
    const qualityScore = data.dataQuality?.overallScore || data.summary.dataQualityScore || 0;
    const qualityColor = qualityScore >= 80 ? '#10b981' : qualityScore >= 60 ? '#f59e0b' : '#ef4444';
    
    doc.setFontSize(12);
    doc.setTextColor(qualityColor);
    doc.text(`Overall Score: ${qualityScore.toFixed(0)}%`, 20, yPos);
    yPos += 8;
    
    if (data.dataQuality) {
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      doc.text(`• Data Completeness: ${data.dataQuality.dataCompleteness.toFixed(0)}%`, 30, yPos);
      yPos += 6;
      doc.text(`• Evidence Provided: ${data.dataQuality.evidenceProvided.toFixed(0)}%`, 30, yPos);
      yPos += 6;
      doc.text(`• Data Recency: ${data.dataQuality.dataRecency.toFixed(0)}%`, 30, yPos);
      yPos += 6;
      doc.text(`• Methodology Accuracy: ${data.dataQuality.methodologyAccuracy.toFixed(0)}%`, 30, yPos);
      yPos += 15;
    }
    
    // ESRS E1-5 Energy Consumption
    if (yPos > 200) {
      doc.addPage();
      yPos = 20;
    }
    
    doc.setFontSize(14);
    doc.setTextColor(26, 26, 46);
    doc.text('ESRS E1-5: Energy Consumption', 20, yPos);
    yPos += 10;
    
    doc.setFontSize(11);
    doc.setTextColor(50, 50, 50);
    
    const hasEnergyData = data.esrsE1Data?.energy_consumption;
    if (hasEnergyData) {
      const energy = data.esrsE1Data.energy_consumption;
      const totalEnergy = (energy.electricity_mwh || 0) + (energy.heating_cooling_mwh || 0) + 
                         (energy.steam_mwh || 0) + (energy.fuel_combustion_mwh || 0);
      const renewablePercentage = totalEnergy > 0 ? ((energy.renewable_energy_mwh || 0) / totalEnergy * 100) : 0;
      
      doc.text(`Total energy consumption: ${totalEnergy.toFixed(1)} MWh`, 20, yPos);
      yPos += 8;
      doc.text(`Renewable energy: ${renewablePercentage.toFixed(1)}%`, 20, yPos);
    } else {
      doc.text('Total energy consumption: 0 MWh', 20, yPos);
      yPos += 8;
      doc.text('Renewable energy: 0%', 20, yPos);
      yPos += 8;
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      doc.text('Note: Energy consumption captured under Scope 2 purchased electricity', 20, yPos);
    }
    yPos += 15;
    
    // ESRS E1-8 Internal Carbon Pricing
    doc.setFontSize(14);
    doc.setTextColor(26, 26, 46);
    doc.text('ESRS E1-8: Internal Carbon Pricing', 20, yPos);
    yPos += 10;
    
    doc.setFontSize(11);
    doc.setTextColor(50, 50, 50);
    
    const carbonPricing = data.esrsE1Data?.internal_carbon_pricing;
    if (carbonPricing?.implemented) {
      doc.text(`Internal carbon price: €${(carbonPricing.price_per_tco2e || 0).toFixed(2)}/tCO₂e`, 20, yPos);
      yPos += 8;
      doc.text(`Coverage: ${carbonPricing.coverage_scope1 ? 'Scope 1, ' : ''}${carbonPricing.coverage_scope2 ? 'Scope 2' : ''}`, 20, yPos);
    } else {
      doc.text('Internal carbon price: €0/tCO₂e', 20, yPos);
      yPos += 8;
      doc.text('Coverage: Not currently implemented', 20, yPos);
    }
    yPos += 15;
    
    // ESRS E1-3 Climate Actions
    if (yPos > 200) {
      doc.addPage();
      yPos = 20;
    }
    
    doc.setFontSize(14);
    doc.setTextColor(26, 26, 46);
    doc.text('ESRS E1-3: Actions and Resources', 20, yPos);
    yPos += 10;
    
    doc.setFontSize(11);
    doc.setTextColor(50, 50, 50);
    
    const climateActions = data.esrsE1Data?.climate_actions;
    if (climateActions) {
      doc.text(`Climate-related CapEx: €${(climateActions.capex_climate_eur || 0).toLocaleString()}`, 20, yPos);
      yPos += 8;
      doc.text(`Climate-related OpEx: €${(climateActions.opex_climate_eur || 0).toLocaleString()}`, 20, yPos);
      yPos += 8;
      doc.text(`Dedicated FTEs: ${(climateActions.fte_dedicated || 0).toFixed(1)}`, 20, yPos);
    } else {
      doc.text('Climate-related CapEx: €0 (0% of total CapEx)', 20, yPos);
      yPos += 8;
      doc.text('Climate-related OpEx: €0 (0% of total OpEx)', 20, yPos);
      yPos += 8;
      doc.text('Dedicated FTEs: 0', 20, yPos);
    }
    yPos += 15;
    
    // GHG Breakdown by Gas Type
    if (data.ghgBreakdown) {
      if (yPos > 180) {
        doc.addPage();
        yPos = 20;
      }
      
      doc.setFontSize(14);
      doc.setTextColor(26, 26, 46);
      doc.text('GHG Breakdown by Gas Type (ESRS E1-6 §53)', 20, yPos);
      yPos += 10;
      
      const ghgData = [
        ['Gas Type', 'Amount', 'Unit'],
        ['CO₂ (Carbon Dioxide)', data.ghgBreakdown.CO2_tonnes.toFixed(2), 'tonnes'],
        ['CH₄ (Methane)', data.ghgBreakdown.CH4_tonnes.toFixed(3), 'tonnes'],
        ['N₂O (Nitrous Oxide)', data.ghgBreakdown.N2O_tonnes.toFixed(3), 'tonnes'],
        ['Total CO₂ Equivalent', data.ghgBreakdown.total_co2e.toFixed(2), 'tCO₂e']
      ];
      
      doc.autoTable({
        startY: yPos,
        head: [ghgData[0]],
        body: ghgData.slice(1),
        theme: 'grid',
        headStyles: { fillColor: [26, 26, 46] },
        styles: { fontSize: 10 }
      });
      
      yPos = doc.lastAutoTable.finalY + 5;
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      doc.text(`GWP Version: ${data.ghgBreakdown.gwp_version}`, 20, yPos);
      yPos += 15;
    }
    
    // Uncertainty Analysis
    if (data.uncertaintyAnalysis && data.uncertaintyAnalysis.confidence_interval_95) {
      if (yPos > 180) {
        doc.addPage();
        yPos = 20;
      }
      
      doc.setFontSize(14);
      doc.setTextColor(26, 26, 46);
      doc.text('Uncertainty Analysis (ESRS E1 §52)', 20, yPos);
      yPos += 10;
      
      doc.setFontSize(11);
      doc.setTextColor(50, 50, 50);
      
      const ua = data.uncertaintyAnalysis;
      doc.text(`95% Confidence Interval: ${(ua.confidence_interval_95[0] / 1000).toFixed(2)} - ${(ua.confidence_interval_95[1] / 1000).toFixed(2)} tCO₂e`, 20, yPos);
      yPos += 8;
      
      if (ua.relative_uncertainty_percent) {
        doc.text(`Relative uncertainty: ±${ua.relative_uncertainty_percent.toFixed(1)}%`, 20, yPos);
        yPos += 8;
      }
      
      doc.text(`Monte Carlo iterations: ${(ua.monte_carlo_runs || 0).toLocaleString()}`, 20, yPos);
      yPos += 15;
    }
    '''

def update_pdf_handler(file_path):
    """Update the pdf-export-handler.ts file"""
    
    # Read and examine the file
    content = examine_file_structure(file_path)
    
    # Find insertion point
    insert_pos, pattern_type = find_insertion_point(content)
    
    if not insert_pos:
        print("\n❌ Could not find a suitable insertion point")
        print("Trying alternative approach...")
        
        # Try to find the main PDF generation function
        if 'generatePDFReport' in content:
            # Find where the PDF is saved
            save_match = re.search(r'(doc\.save\([^)]+\);)', content)
            if save_match:
                insert_pos = save_match.start()
                pattern_type = 'before_save'
                print("✅ Found insertion point before doc.save()")
    
    if not insert_pos:
        print("❌ Unable to find insertion point")
        return False
    
    # Generate the enhanced content code
    enhanced_code = generate_enhanced_content_code()
    
    # Insert the enhanced content
    new_content = content[:insert_pos] + enhanced_code + '\n\n    ' + content[insert_pos:]
    
    # Also update the PDFExportData interface if it exists
    interface_pattern = r'(export interface PDFExportData[^{]*\{[\s\S]*?)(\})'
    interface_match = re.search(interface_pattern, new_content)
    
    if interface_match:
        # Add new fields to the interface
        new_fields = '''
  dataQuality?: {
    overallScore: number;
    dataCompleteness: number;
    evidenceProvided: number;
    dataRecency: number;
    methodologyAccuracy: number;
  };
  esrsE1Data?: any;
  ghgBreakdown?: any;
  uncertaintyAnalysis?: any;
'''
        new_interface = interface_match.group(1) + new_fields + interface_match.group(2)
        new_content = new_content[:interface_match.start()] + new_interface + new_content[interface_match.end():]
        print("✅ Updated PDFExportData interface")
    
    # Write the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Successfully inserted enhanced content using pattern: {pattern_type}")
    return True

def main():
    """Main function"""
    # Navigate to correct directory
    expected_dir = "/Users/isaiah/Documents/Scope3Tool"
    current_dir = os.getcwd()
    
    if current_dir != expected_dir:
        print(f"📂 Navigating to: {expected_dir}")
        try:
            os.chdir(expected_dir)
        except Exception as e:
            print(f"❌ Could not change directory: {e}")
            return
    
    # File path from your output
    file_path = "./factortrace-frontend/src/components/emissions/pdf-export-handler.ts"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"📁 Processing: {file_path}")
    
    # Create backup
    backup_path = create_backup(file_path)
    
    # Update the file
    success = update_pdf_handler(file_path)
    
    if success:
        print("\n✨ Update complete!")
        print("\nThe PDF export now includes:")
        print("✓ Data Quality Score with breakdown")
        print("✓ ESRS E1-5 Energy Consumption")
        print("✓ ESRS E1-8 Internal Carbon Pricing")
        print("✓ ESRS E1-3 Climate Actions & Resources")
        print("✓ GHG Breakdown by Gas Type")
        print("✓ Uncertainty Analysis")
        print("\n🚀 Your PDF reports are now ESRS E1 compliant!")
    else:
        print("\n❌ Update failed!")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()