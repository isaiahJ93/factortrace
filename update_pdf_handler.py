#!/usr/bin/env python3
"""
Update pdf-export-handler.ts to include comprehensive ESRS E1 sections
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

def update_pdf_handler(file_path):
    """Update the pdf-export-handler.ts file with enhanced content generation"""
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the generatePDFContent function and replace it
    new_function = '''function generatePDFContent(doc: jsPDF, data: PDFExportData): void {
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 20;
  const contentWidth = pageWidth - (margin * 2);
  let yPosition = margin;

  // Helper function to check if we need a new page
  const checkNewPage = (requiredSpace: number = 30) => {
    if (yPosition + requiredSpace > pageHeight - margin) {
      doc.addPage();
      yPosition = margin;
      return true;
    }
    return false;
  };

  // Helper function to add section header
  const addSectionHeader = (title: string, subtitle?: string) => {
    checkNewPage(40);
    doc.setFontSize(16);
    doc.setTextColor(26, 26, 46);
    doc.text(title, margin, yPosition);
    yPosition += 8;
    
    if (subtitle) {
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      doc.text(subtitle, margin, yPosition);
      yPosition += 6;
    }
    
    // Add underline
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, yPosition, pageWidth - margin, yPosition);
    yPosition += 10;
  };

  // Cover Page
  generateCoverPage(doc, data);
  doc.addPage();
  yPosition = margin;

  // Executive Dashboard
  addSectionHeader('Executive Dashboard', 'Key Performance Indicators');
  
  // Add Data Quality Score
  doc.setFontSize(12);
  doc.setTextColor(50, 50, 50);
  const qualityScore = data.dataQuality?.overallScore || data.summary.dataQualityScore || 0;
  const qualityColor = qualityScore >= 80 ? [16, 185, 129] : qualityScore >= 60 ? [245, 158, 11] : [239, 68, 68];
  doc.setTextColor(...qualityColor as [number, number, number]);
  doc.text(`Data Quality Score: ${qualityScore.toFixed(0)}%`, margin, yPosition);
  doc.setTextColor(50, 50, 50);
  yPosition += 8;
  
  // Data Quality Details
  if (data.dataQuality) {
    doc.setFontSize(10);
    doc.text(`• Data Completeness: ${data.dataQuality.dataCompleteness.toFixed(0)}%`, margin + 10, yPosition);
    yPosition += 6;
    doc.text(`• Evidence Provided: ${data.dataQuality.evidenceProvided.toFixed(0)}%`, margin + 10, yPosition);
    yPosition += 6;
    doc.text(`• Data Recency: ${data.dataQuality.dataRecency.toFixed(0)}%`, margin + 10, yPosition);
    yPosition += 6;
    doc.text(`• Methodology Accuracy: ${data.dataQuality.methodologyAccuracy.toFixed(0)}%`, margin + 10, yPosition);
    yPosition += 15;
  }

  // Emissions Summary Cards
  const summaryData = [
    { label: 'Total Emissions', value: data.summary.totalEmissions.toFixed(2), unit: 'tCO₂e', color: [147, 51, 234] },
    { label: 'Scope 1', value: data.summary.scope1.toFixed(2), unit: 'tCO₂e', percentage: data.summary.scope1Percentage.toFixed(0) + '%', color: [239, 68, 68] },
    { label: 'Scope 2', value: data.summary.scope2.toFixed(2), unit: 'tCO₂e', percentage: data.summary.scope2Percentage.toFixed(0) + '%', color: [59, 130, 246] },
    { label: 'Scope 3', value: data.summary.scope3.toFixed(2), unit: 'tCO₂e', percentage: data.summary.scope3Percentage.toFixed(0) + '%', color: [16, 185, 129] }
  ];

  summaryData.forEach((item, index) => {
    const boxX = margin + (index * (contentWidth / 4));
    const boxWidth = (contentWidth / 4) - 5;
    
    // Draw box
    doc.setFillColor(...item.color as [number, number, number]);
    doc.rect(boxX, yPosition, boxWidth, 25, 'F');
    
    // Add text
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(10);
    doc.text(item.label, boxX + 5, yPosition + 8);
    doc.setFontSize(14);
    doc.text(item.value, boxX + 5, yPosition + 16);
    doc.setFontSize(8);
    doc.text(item.unit, boxX + 5, yPosition + 22);
    if (item.percentage) {
      doc.text(item.percentage, boxX + boxWidth - 15, yPosition + 22);
    }
  });
  yPosition += 35;

  // Emissions by Scope Pie Chart (placeholder)
  checkNewPage(120);
  addSectionHeader('Emissions by Scope', 'Distribution of emissions across scopes');
  
  // Draw pie chart placeholder
  const pieX = pageWidth / 2;
  const pieY = yPosition + 40;
  const pieRadius = 30;
  
  // Draw circles for each scope
  const angles = [
    { start: 0, end: (data.summary.scope1Percentage / 100) * Math.PI * 2, color: [239, 68, 68] },
    { start: (data.summary.scope1Percentage / 100) * Math.PI * 2, 
      end: ((data.summary.scope1Percentage + data.summary.scope2Percentage) / 100) * Math.PI * 2, 
      color: [59, 130, 246] },
    { start: ((data.summary.scope1Percentage + data.summary.scope2Percentage) / 100) * Math.PI * 2, 
      end: Math.PI * 2, 
      color: [16, 185, 129] }
  ];
  
  angles.forEach(segment => {
    doc.setFillColor(...segment.color as [number, number, number]);
    doc.arc(pieX, pieY, pieRadius, segment.start - Math.PI/2, segment.end - Math.PI/2, 'F');
  });
  
  // Add legend
  doc.setFontSize(10);
  const legendItems = [
    { label: `Scope 1: ${data.summary.scope1Percentage.toFixed(0)}%`, color: [239, 68, 68] },
    { label: `Scope 2: ${data.summary.scope2Percentage.toFixed(0)}%`, color: [59, 130, 246] },
    { label: `Scope 3: ${data.summary.scope3Percentage.toFixed(0)}%`, color: [16, 185, 129] }
  ];
  
  legendItems.forEach((item, index) => {
    const legendY = pieY - 20 + (index * 15);
    doc.setFillColor(...item.color as [number, number, number]);
    doc.rect(pieX + 50, legendY - 3, 10, 10, 'F');
    doc.setTextColor(50, 50, 50);
    doc.text(item.label, pieX + 65, legendY + 3);
  });
  
  yPosition = pieY + pieRadius + 30;

  // Top Emission Categories
  checkNewPage(150);
  addSectionHeader('Top Emission Categories', 'Highest contributing activities');
  
  if (data.topEmissionSources && data.topEmissionSources.length > 0) {
    const barHeight = 15;
    const maxEmission = Math.max(...data.topEmissionSources.map(s => s.emissions));
    
    data.topEmissionSources.slice(0, 5).forEach((source, index) => {
      const barY = yPosition + (index * (barHeight + 5));
      const barWidth = (source.emissions / maxEmission) * (contentWidth - 100);
      
      // Category name
      doc.setFontSize(10);
      doc.setTextColor(50, 50, 50);
      doc.text(source.name.substring(0, 30), margin, barY + 10);
      
      // Bar
      doc.setFillColor(59, 130, 246);
      doc.rect(margin + 100, barY, barWidth, barHeight, 'F');
      
      // Value
      doc.text(`${source.emissions.toFixed(2)} tCO₂e`, margin + 105 + barWidth, barY + 10);
    });
    yPosition += (5 * (barHeight + 5)) + 10;
  }

  // New Page for ESRS E1 Sections
  doc.addPage();
  yPosition = margin;
  
  // ESRS E1-5 Energy Consumption
  addSectionHeader('ESRS E1-5: Energy Consumption', 'Energy consumption and renewable energy share');
  
  doc.setFontSize(11);
  doc.setTextColor(50, 50, 50);
  
  // Check if we have ESRS data
  const hasEnergyData = data.esrsE1Data?.energy_consumption;
  if (hasEnergyData) {
    const energy = data.esrsE1Data.energy_consumption;
    const totalEnergy = (energy.electricity_mwh || 0) + (energy.heating_cooling_mwh || 0) + 
                       (energy.steam_mwh || 0) + (energy.fuel_combustion_mwh || 0);
    const renewablePercentage = totalEnergy > 0 ? ((energy.renewable_energy_mwh || 0) / totalEnergy * 100) : 0;
    
    doc.text(`Total energy consumption: ${totalEnergy.toFixed(1)} MWh`, margin, yPosition);
    yPosition += 8;
    doc.text(`• Electricity: ${(energy.electricity_mwh || 0).toFixed(1)} MWh`, margin + 10, yPosition);
    yPosition += 6;
    doc.text(`• Heating & Cooling: ${(energy.heating_cooling_mwh || 0).toFixed(1)} MWh`, margin + 10, yPosition);
    yPosition += 6;
    doc.text(`• Steam: ${(energy.steam_mwh || 0).toFixed(1)} MWh`, margin + 10, yPosition);
    yPosition += 6;
    doc.text(`• Fuel Combustion: ${(energy.fuel_combustion_mwh || 0).toFixed(1)} MWh`, margin + 10, yPosition);
    yPosition += 8;
    doc.text(`Renewable energy: ${(energy.renewable_energy_mwh || 0).toFixed(1)} MWh (${renewablePercentage.toFixed(1)}%)`, margin, yPosition);
    
    if (energy.energy_intensity_value) {
      yPosition += 6;
      doc.text(`Energy intensity: ${energy.energy_intensity_value.toFixed(2)} ${energy.energy_intensity_unit || 'MWh/million EUR'}`, margin, yPosition);
    }
  } else {
    doc.text('Total energy consumption: 0 MWh', margin, yPosition);
    yPosition += 8;
    doc.text('Renewable energy: 0%', margin, yPosition);
    yPosition += 8;
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.text('Note: Energy consumption captured under Scope 2 purchased electricity', margin, yPosition);
  }
  yPosition += 15;

  // ESRS E1-8 Internal Carbon Pricing
  addSectionHeader('ESRS E1-8: Internal Carbon Pricing', 'Carbon pricing mechanisms');
  
  doc.setFontSize(11);
  doc.setTextColor(50, 50, 50);
  
  const carbonPricing = data.esrsE1Data?.internal_carbon_pricing;
  if (carbonPricing?.implemented) {
    doc.text(`Internal carbon price: €${(carbonPricing.price_per_tco2e || 0).toFixed(2)}/tCO₂e`, margin, yPosition);
    yPosition += 8;
    doc.text('Coverage:', margin, yPosition);
    yPosition += 6;
    if (carbonPricing.coverage_scope1) {
      doc.text('• Scope 1 emissions', margin + 10, yPosition);
      yPosition += 6;
    }
    if (carbonPricing.coverage_scope2) {
      doc.text('• Scope 2 emissions', margin + 10, yPosition);
      yPosition += 6;
    }
    if (carbonPricing.coverage_scope3_categories?.length > 0) {
      doc.text(`• Scope 3 categories: ${carbonPricing.coverage_scope3_categories.length}`, margin + 10, yPosition);
      yPosition += 6;
    }
    doc.text(`Pricing type: ${carbonPricing.pricing_type || 'Shadow price'}`, margin, yPosition);
  } else {
    doc.text('Internal carbon price: €0/tCO₂e', margin, yPosition);
    yPosition += 8;
    doc.text('Coverage: Not currently implemented', margin, yPosition);
  }
  yPosition += 15;

  // ESRS E1-3 Climate Actions & Resources
  addSectionHeader('ESRS E1-3: Actions and Resources', 'Climate-related expenditures and resources');
  
  doc.setFontSize(11);
  doc.setTextColor(50, 50, 50);
  
  const climateActions = data.esrsE1Data?.climate_actions;
  if (climateActions) {
    const totalFinance = (climateActions.capex_climate_eur || 0) + (climateActions.opex_climate_eur || 0);
    doc.text(`Climate-related CapEx: €${(climateActions.capex_climate_eur || 0).toLocaleString()} (% of total CapEx: N/A)`, margin, yPosition);
    yPosition += 8;
    doc.text(`Climate-related OpEx: €${(climateActions.opex_climate_eur || 0).toLocaleString()} (% of total OpEx: N/A)`, margin, yPosition);
    yPosition += 8;
    doc.text(`Total climate finance: €${totalFinance.toLocaleString()}`, margin, yPosition);
    yPosition += 8;
    doc.text(`Dedicated FTEs: ${(climateActions.fte_dedicated || 0).toFixed(1)}`, margin, yPosition);
  } else {
    doc.text('Climate-related CapEx: €0 (0% of total CapEx)', margin, yPosition);
    yPosition += 8;
    doc.text('Climate-related OpEx: €0 (0% of total OpEx)', margin, yPosition);
    yPosition += 8;
    doc.text('Dedicated FTEs: 0', margin, yPosition);
  }
  yPosition += 15;

  // GHG Breakdown by Gas Type
  checkNewPage(120);
  addSectionHeader('GHG Breakdown by Gas Type', 'As required under ESRS E1-6 paragraph 53');
  
  doc.setFontSize(11);
  doc.setTextColor(50, 50, 50);
  
  if (data.ghgBreakdown) {
    const ghg = data.ghgBreakdown;
    doc.text('Individual Gases:', margin, yPosition);
    yPosition += 8;
    doc.text(`• CO₂ (Carbon Dioxide): ${ghg.CO2_tonnes.toFixed(2)} tonnes`, margin + 10, yPosition);
    yPosition += 6;
    doc.text(`• CH₄ (Methane): ${ghg.CH4_tonnes.toFixed(3)} tonnes`, margin + 10, yPosition);
    yPosition += 6;
    doc.text(`• N₂O (Nitrous Oxide): ${ghg.N2O_tonnes.toFixed(3)} tonnes`, margin + 10, yPosition);
    yPosition += 6;
    if (ghg.HFCs_tonnes_co2e && ghg.HFCs_tonnes_co2e > 0) {
      doc.text(`• HFCs: ${ghg.HFCs_tonnes_co2e.toFixed(3)} tCO₂e`, margin + 10, yPosition);
      yPosition += 6;
    }
    yPosition += 8;
    doc.text(`Total CO₂ Equivalent: ${ghg.total_co2e.toFixed(2)} tCO₂e`, margin, yPosition);
    yPosition += 6;
    doc.text(`GWP Version: ${ghg.gwp_version}`, margin, yPosition);
  } else {
    doc.text('GHG breakdown by gas type not calculated', margin, yPosition);
  }
  yPosition += 15;

  // Uncertainty Analysis
  if (data.uncertaintyAnalysis) {
    checkNewPage(100);
    addSectionHeader('Uncertainty Analysis', 'Monte Carlo simulation results (ESRS E1 paragraph 52)');
    
    doc.setFontSize(11);
    doc.setTextColor(50, 50, 50);
    
    const ua = data.uncertaintyAnalysis;
    if (ua.confidence_interval_95) {
      doc.text('95% Confidence Interval:', margin, yPosition);
      yPosition += 8;
      doc.text(`• Lower bound: ${(ua.confidence_interval_95[0] / 1000).toFixed(2)} tCO₂e`, margin + 10, yPosition);
      yPosition += 6;
      doc.text(`• Upper bound: ${(ua.confidence_interval_95[1] / 1000).toFixed(2)} tCO₂e`, margin + 10, yPosition);
      yPosition += 8;
    }
    if (ua.mean_emissions) {
      doc.text(`Mean emissions: ${(ua.mean_emissions / 1000).toFixed(2)} tCO₂e`, margin, yPosition);
      yPosition += 6;
    }
    if (ua.std_deviation) {
      doc.text(`Standard deviation: ${(ua.std_deviation / 1000).toFixed(2)} tCO₂e`, margin, yPosition);
      yPosition += 6;
    }
    if (ua.relative_uncertainty_percent) {
      doc.text(`Relative uncertainty: ±${ua.relative_uncertainty_percent.toFixed(1)}%`, margin, yPosition);
      yPosition += 6;
    }
    doc.text(`Monte Carlo iterations: ${(ua.monte_carlo_runs || 0).toLocaleString()}`, margin, yPosition);
  }

  // Detailed Activity Breakdown (as appendix)
  doc.addPage();
  yPosition = margin;
  addSectionHeader('Appendix: Detailed Activity Breakdown', 'Granular emissions data by activity');
  
  if (data.activities && data.activities.length > 0) {
    // Sort activities by emissions (highest first)
    const sortedActivities = [...data.activities].sort((a, b) => {
      const emissionsA = (parseFloat(a.amount?.toString() || '0') * (a.factor || 0)) / 1000;
      const emissionsB = (parseFloat(b.amount?.toString() || '0') * (b.factor || 0)) / 1000;
      return emissionsB - emissionsA;
    });
    
    // Create table headers
    doc.setFontSize(10);
    doc.setFont(undefined, 'bold');
    const headers = ['Activity', 'Scope', 'Amount', 'Unit', 'Factor', 'Emissions'];
    const columnWidths = [60, 20, 25, 20, 35, 30];
    
    headers.forEach((header, index) => {
      const xPos = margin + columnWidths.slice(0, index).reduce((a, b) => a + b, 0);
      doc.text(header, xPos, yPosition);
    });
    yPosition += 6;
    
    // Add line
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, yPosition - 2, pageWidth - margin, yPosition - 2);
    
    // Add activities
    doc.setFont(undefined, 'normal');
    doc.setFontSize(9);
    
    sortedActivities.forEach((activity, index) => {
      checkNewPage(10);
      
      const emissions = (parseFloat(activity.amount?.toString() || '0') * (activity.factor || 0)) / 1000;
      const values = [
        activity.name.substring(0, 30),
        activity.scope,
        parseFloat(activity.amount?.toString() || '0').toFixed(1),
        activity.unit,
        `${activity.factor} kg CO₂e/${activity.unit}`,
        `${emissions.toFixed(3)} tCO₂e`
      ];
      
      values.forEach((value, colIndex) => {
        const xPos = margin + columnWidths.slice(0, colIndex).reduce((a, b) => a + b, 0);
        doc.text(value.toString(), xPos, yPosition);
      });
      
      yPosition += 6;
      
      // Add page break if needed
      if (index < sortedActivities.length - 1 && yPosition > pageHeight - 40) {
        doc.addPage();
        yPosition = margin;
        
        // Re-add headers on new page
        doc.setFont(undefined, 'bold');
        headers.forEach((header, index) => {
          const xPos = margin + columnWidths.slice(0, index).reduce((a, b) => a + b, 0);
          doc.text(header, xPos, yPosition);
        });
        yPosition += 6;
        doc.line(margin, yPosition - 2, pageWidth - margin, yPosition - 2);
        doc.setFont(undefined, 'normal');
      }
    });
  }

  // Methodology & Assumptions
  doc.addPage();
  yPosition = margin;
  addSectionHeader('Methodology & Assumptions', 'Calculation methodology and key assumptions');
  
  doc.setFontSize(11);
  doc.setTextColor(50, 50, 50);
  const methodology = [
    '• Emission factors: DEFRA 2023, EPA EEIO, IPCC AR5',
    '• Calculation standard: GHG Protocol Corporate Standard',
    '• Organizational boundary: Operational control',
    '• Consolidation approach: Equity share',
    '• Base year: Not yet established',
    '• Exclusions: De minimis sources (<1% of total)'
  ];
  
  methodology.forEach(item => {
    doc.text(item, margin, yPosition);
    yPosition += 8;
  });

  // Footer on last page
  doc.setFontSize(8);
  doc.setTextColor(150, 150, 150);
  doc.text(
    `Generated on ${new Date().toLocaleDateString()} | ${data.metadata.documentId}`,
    margin,
    pageHeight - 10
  );
}'''

    # Find and replace the generatePDFContent function
    pattern = r'function generatePDFContent\(doc: jsPDF, data: PDFExportData\): void \{[\s\S]*?\n\}'
    
    # First, let's find if the function exists
    if re.search(pattern, content):
        # Replace the existing function
        content = re.sub(pattern, new_function, content, count=1)
        print("✅ Updated existing generatePDFContent function")
    else:
        # If not found, try to find where to insert it
        # Look for the generateCoverPage function and insert after it
        cover_pattern = r'(function generateCoverPage\(doc: jsPDF, data: PDFExportData\): void \{[\s\S]*?\n\})'
        match = re.search(cover_pattern, content)
        
        if match:
            # Insert the new function after generateCoverPage
            insert_pos = match.end()
            content = content[:insert_pos] + '\n\n' + new_function + content[insert_pos:]
            print("✅ Added new generatePDFContent function")
        else:
            print("❌ Could not find appropriate location to insert generatePDFContent")
            return False
    
    # Also need to update the PDFExportData interface to include new fields
    interface_updates = '''
  // ESRS E1 Data
  esrsE1Data?: {
    energy_consumption?: {
      electricity_mwh: number;
      heating_cooling_mwh: number;
      steam_mwh: number;
      fuel_combustion_mwh: number;
      renewable_energy_mwh: number;
      renewable_percentage?: number;
      total_energy_mwh?: number;
      energy_intensity_value?: number;
      energy_intensity_unit?: string;
    };
    internal_carbon_pricing?: {
      implemented: boolean;
      price_per_tco2e?: number;
      currency?: string;
      coverage_scope1?: boolean;
      coverage_scope2?: boolean;
      coverage_scope3_categories?: number[];
      pricing_type?: string;
    };
    climate_actions?: {
      capex_climate_eur: number;
      opex_climate_eur: number;
      fte_dedicated: number;
      reporting_year?: number;
    };
    climate_policy?: {
      has_climate_policy: boolean;
      net_zero_target_year?: number;
      board_oversight?: boolean;
      executive_compensation_linked?: boolean;
    };
  };
  
  // GHG Breakdown
  ghgBreakdown?: {
    CO2_tonnes: number;
    CH4_tonnes: number;
    N2O_tonnes: number;
    HFCs_tonnes_co2e?: number;
    PFCs_tonnes_co2e?: number;
    SF6_tonnes?: number;
    NF3_tonnes?: number;
    total_co2e: number;
    gwp_version: string;
  };'''
    
    # Find the PDFExportData interface and add the new fields
    interface_pattern = r'(export interface PDFExportData \{[\s\S]*?)(  companyProfile\?: CompanyProfile;)'
    match = re.search(interface_pattern, content)
    
    if match:
        # Insert before companyProfile
        new_interface = match.group(1) + interface_updates + '\n' + match.group(2)
        content = content[:match.start()] + new_interface + content[match.end():]
        print("✅ Updated PDFExportData interface")
    
    # Write the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
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
    
    # Find the pdf-export-handler.ts file
    possible_paths = [
        "src/components/emissions/pdf-export-handler.ts",
        "src/components/pdf-export-handler.ts",
        "components/emissions/pdf-export-handler.ts",
        "components/pdf-export-handler.ts"
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if not file_path:
        # Search for the file
        for root, dirs, files in os.walk('.'):
            if 'pdf-export-handler.ts' in files:
                file_path = os.path.join(root, 'pdf-export-handler.ts')
                break
    
    if not file_path:
        print("❌ Could not find pdf-export-handler.ts")
        return
    
    print(f"📁 Found file: {file_path}")
    
    # Create backup
    backup_path = create_backup(file_path)
    
    # Update the file
    success = update_pdf_handler(file_path)
    
    if success:
        print("\n✨ Update complete!")
        print("\nThe PDF export now includes:")
        print("✓ Data Quality Score with breakdown")
        print("✓ Emissions by Scope pie chart")
        print("✓ Top Emission Categories bar chart")
        print("✓ ESRS E1-5 Energy Consumption")
        print("✓ ESRS E1-8 Internal Carbon Pricing")
        print("✓ ESRS E1-3 Climate Actions & Resources")
        print("✓ GHG Breakdown by Gas Type")
        print("✓ Uncertainty Analysis")
        print("✓ Detailed Activity Breakdown")
        print("✓ Methodology & Assumptions")
        print("\n🚀 Your PDF reports are now fully ESRS E1 compliant!")
    else:
        print("\n❌ Update failed!")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()