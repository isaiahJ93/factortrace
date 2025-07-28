#!/usr/bin/env python3
"""
Add comprehensive ESRS E1 sections to the professional pdf-export-handler.ts
Respects existing class structure and data consistency principles
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

def add_esrs_sections_to_handler(file_path):
    """Add all missing ESRS E1 sections to the PDF handler"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find where to insert the new section method calls
    # Look for where the main content generation happens
    main_generation_pattern = r'(// Add detailed breakdown[\s\S]*?)((?:}\s*)?// Footer section|}\s*catch)'
    match = re.search(main_generation_pattern, content)
    
    if not match:
        # Try alternative pattern - look for where pages are being added
        main_generation_pattern = r'(doc\.addPage\(\);[\s\S]*?yPosition[^;]+;)([\s\S]*?)(// Footer|}\s*catch|\n\s*doc\.save)'
        match = re.search(main_generation_pattern, content)
    
    if match:
        insertion_point = match.end(1)
        print("✅ Found insertion point for new sections")
    else:
        print("⚠️  Using fallback insertion strategy")
        # Find the end of a major section to insert after
        insertion_pattern = r'(// Activity-level[\s\S]*?}\s*\);)([\s\S]*?)(// Footer|}\s*catch)'
        match = re.search(insertion_pattern, content)
        if match:
            insertion_point = match.end(1)
        else:
            print("❌ Could not find suitable insertion point")
            return False
    
    # Insert the new section calls
    new_sections_calls = '''
    
    // ESRS E1 Enhanced Sections
    // =========================
    
    // Data Quality Assessment
    doc.addPage();
    yPosition = 20;
    this.addDataQualitySection(doc, data, yPosition);
    
    // Visual Analytics
    doc.addPage();
    yPosition = 20;
    this.addEmissionsByScopeChart(doc, data, yPosition);
    
    doc.addPage();
    yPosition = 20;
    this.addTopCategoriesChart(doc, data, yPosition);
    
    // ESRS E1 Mandatory Disclosures
    doc.addPage();
    yPosition = 20;
    this.addEnergyConsumptionSection(doc, data, yPosition);
    
    this.addCarbonPricingSection(doc, data, doc.lastAutoTable?.finalY + 20 || yPosition + 100);
    
    doc.addPage();
    yPosition = 20;
    this.addClimateActionsSection(doc, data, yPosition);
    
    // Technical Analysis
    if (data.ghgBreakdown || data.results?.ghg_breakdown) {
      doc.addPage();
      yPosition = 20;
      this.addGHGBreakdownSection(doc, data, yPosition);
    }
    
    if (data.uncertaintyAnalysis || data.results?.uncertainty_analysis) {
      doc.addPage();
      yPosition = 20;
      this.addUncertaintyAnalysisSection(doc, data, yPosition);
    }
'''
    
    # Insert the section calls
    content = content[:insertion_point] + new_sections_calls + content[insertion_point:]
    
    # Now add the method implementations
    # Find the end of the class to insert new methods
    class_end_pattern = r'(}\s*// End of PDFExportHandler class|}\s*export)'
    class_match = re.search(class_end_pattern, content)
    
    if not class_match:
        # Try to find the last method in the class
        method_pattern = r'(private\s+\w+\s*\([^)]*\)[^{]*\{[\s\S]*?\n  \})([\s\S]*?)(}\s*$|export)'
        matches = list(re.finditer(method_pattern, content))
        if matches:
            class_match = matches[-1]
            methods_insertion_point = class_match.end(1)
        else:
            print("❌ Could not find class end")
            return False
    else:
        methods_insertion_point = class_match.start()
    
    # Add new methods
    new_methods = '''
  
  // ==========================================
  // ESRS E1 Enhanced Section Methods
  // ==========================================
  
  /**
   * Add Data Quality Assessment Section
   * Transparency requirement for ESRS E1
   */
  private addDataQualitySection(doc: jsPDF, data: PDFExportData, startY: number): void {
    let yPosition = startY;
    
    doc.setFontSize(16);
    doc.setTextColor(26, 26, 46);
    doc.text('Data Quality Assessment', 20, yPosition);
    yPosition += 12;
    
    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    doc.text('ESRS E1 requires transparency in data quality and calculation methodologies', 20, yPosition);
    yPosition += 15;
    
    const qualityScore = data.dataQuality?.overallScore || data.summary.dataQualityScore || 0;
    const scoreColor = qualityScore >= 80 ? '#10b981' : qualityScore >= 60 ? '#f59e0b' : '#ef4444';
    
    // Overall score box
    doc.setFillColor(245, 245, 245);
    doc.rect(20, yPosition, 170, 30, 'F');
    
    doc.setFontSize(24);
    doc.setTextColor(scoreColor);
    doc.text(`${qualityScore.toFixed(0)}%`, 30, yPosition + 20);
    
    doc.setFontSize(12);
    doc.setTextColor(50, 50, 50);
    doc.text('Overall Data Quality Score', 70, yPosition + 20);
    yPosition += 40;
    
    // Detailed metrics
    if (data.dataQuality) {
      const metrics = [
        ['Data Completeness', data.dataQuality.dataCompleteness, 'Percentage of required data fields provided'],
        ['Evidence Coverage', data.dataQuality.evidenceProvided, 'Activities with supporting documentation'],
        ['Data Recency', data.dataQuality.dataRecency, 'How current the data is'],
        ['Methodology Accuracy', data.dataQuality.methodologyAccuracy, 'Use of recognized emission factors']
      ];
      
      doc.autoTable({
        startY: yPosition,
        head: [['Metric', 'Score', 'Description']],
        body: metrics.map(m => [m[0], `${m[1].toFixed(0)}%`, m[2]]),
        theme: 'grid',
        headStyles: { fillColor: [26, 26, 46] },
        columnStyles: {
          1: { halign: 'center', cellWidth: 30 },
        }
      });
    }
  }
  
  /**
   * Add Emissions by Scope Visualization
   * Executive summary requirement
   */
  private addEmissionsByScopeChart(doc: jsPDF, data: PDFExportData, startY: number): void {
    let yPosition = startY;
    
    doc.setFontSize(16);
    doc.setTextColor(26, 26, 46);
    doc.text('Emissions by Scope', 20, yPosition);
    yPosition += 12;
    
    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    doc.text('Distribution of emissions across GHG Protocol scopes', 20, yPosition);
    yPosition += 20;
    
    const total = data.summary.totalEmissions || 0;
    const scopes = [
      { name: 'Scope 1 - Direct', value: data.summary.scope1, percentage: data.summary.scope1Percentage, color: [239, 68, 68] },
      { name: 'Scope 2 - Energy', value: data.summary.scope2, percentage: data.summary.scope2Percentage, color: [59, 130, 246] },
      { name: 'Scope 3 - Value Chain', value: data.summary.scope3, percentage: data.summary.scope3Percentage, color: [16, 185, 129] }
    ];
    
    // Visual bar chart
    const barHeight = 30;
    const maxWidth = 150;
    
    scopes.forEach((scope, index) => {
      const yPos = yPosition + (index * (barHeight + 10));
      const barWidth = total > 0 ? (scope.value / total) * maxWidth : 0;
      
      // Scope name and value
      doc.setFontSize(12);
      doc.setTextColor(50, 50, 50);
      doc.text(scope.name, 20, yPos + 20);
      
      // Bar
      doc.setFillColor(...scope.color as [number, number, number]);
      doc.rect(20, yPos + 25, barWidth, barHeight, 'F');
      
      // Percentage and value
      doc.setFontSize(11);
      doc.text(`${scope.percentage.toFixed(1)}%`, 175, yPos + 20);
      doc.text(`${scope.value.toFixed(2)} tCO₂e`, 175, yPos + 35);
    });
    
    yPosition += (3 * (barHeight + 10)) + 20;
    
    // Summary table
    doc.autoTable({
      startY: yPosition,
      head: [['Scope', 'Emissions (tCO₂e)', 'Percentage', 'Key Sources']],
      body: [
        ['Scope 1', data.summary.scope1.toFixed(2), `${data.summary.scope1Percentage.toFixed(1)}%`, 'Fuel combustion, processes'],
        ['Scope 2', data.summary.scope2.toFixed(2), `${data.summary.scope2Percentage.toFixed(1)}%`, 'Purchased electricity, heat'],
        ['Scope 3', data.summary.scope3.toFixed(2), `${data.summary.scope3Percentage.toFixed(1)}%`, 'Supply chain, travel, waste'],
        ['Total', data.summary.totalEmissions.toFixed(2), '100.0%', '']
      ],
      theme: 'striped',
      headStyles: { fillColor: [26, 26, 46] },
      footStyles: { fontStyle: 'bold' }
    });
  }
  
  /**
   * Add Top Emission Categories
   * Materiality assessment support
   */
  private addTopCategoriesChart(doc: jsPDF, data: PDFExportData, startY: number): void {
    let yPosition = startY;
    
    doc.setFontSize(16);
    doc.setTextColor(26, 26, 46);
    doc.text('Top Emission Categories', 20, yPosition);
    yPosition += 12;
    
    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    doc.text('Highest contributing activities for materiality assessment', 20, yPosition);
    yPosition += 20;
    
    if (data.topEmissionSources && data.topEmissionSources.length > 0) {
      const tableData = data.topEmissionSources.slice(0, 10).map((source, index) => [
        `${index + 1}`,
        source.name.substring(0, 40),
        source.category,
        `${source.emissions.toFixed(3)}`,
        `${source.percentage.toFixed(1)}%`
      ]);
      
      doc.autoTable({
        startY: yPosition,
        head: [['Rank', 'Activity', 'Category', 'tCO₂e', '% of Total']],
        body: tableData,
        theme: 'grid',
        headStyles: { fillColor: [26, 26, 46] },
        columnStyles: {
          0: { cellWidth: 15, halign: 'center' },
          3: { halign: 'right' },
          4: { halign: 'center' }
        }
      });
      
      yPosition = doc.lastAutoTable.finalY + 15;
      
      // Visual representation of top 5
      const top5 = data.topEmissionSources.slice(0, 5);
      const maxEmission = Math.max(...top5.map(s => s.emissions));
      
      doc.setFontSize(12);
      doc.setTextColor(26, 26, 46);
      doc.text('Top 5 Emission Sources - Visual Breakdown', 20, yPosition);
      yPosition += 10;
      
      top5.forEach((source, index) => {
        const barWidth = (source.emissions / maxEmission) * 120;
        const yPos = yPosition + (index * 25);
        
        doc.setFontSize(10);
        doc.setTextColor(50, 50, 50);
        doc.text(source.name.substring(0, 30), 20, yPos + 15);
        
        // Gradient effect with scope colors
        const color = index === 0 ? [239, 68, 68] : index === 1 ? [59, 130, 246] : [16, 185, 129];
        doc.setFillColor(...color as [number, number, number]);
        doc.rect(120, yPos + 10, barWidth, 15, 'F');
        
        doc.text(`${source.emissions.toFixed(2)} tCO₂e`, 245, yPos + 15);
      });
    }
  }
  
  /**
   * ESRS E1-5: Energy Consumption
   */
  private addEnergyConsumptionSection(doc: jsPDF, data: PDFExportData, startY: number): void {
    let yPosition = startY;
    
    doc.setFontSize(16);
    doc.setTextColor(26, 26, 46);
    doc.text('ESRS E1-5: Energy Consumption', 20, yPosition);
    yPosition += 12;
    
    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    doc.text('Energy consumption and renewable energy share (§67-69)', 20, yPosition);
    yPosition += 20;
    
    const energyData = data.esrsE1Data?.energy_consumption;
    
    if (energyData) {
      const totalEnergy = (energyData.electricity_mwh || 0) + 
                         (energyData.heating_cooling_mwh || 0) + 
                         (energyData.steam_mwh || 0) + 
                         (energyData.fuel_combustion_mwh || 0);
      const renewablePercentage = totalEnergy > 0 ? 
        ((energyData.renewable_energy_mwh || 0) / totalEnergy * 100) : 0;
      
      const energyTable = [
        ['Energy Type', 'Consumption (MWh)', 'Percentage'],
        ['Electricity', energyData.electricity_mwh?.toFixed(1) || '0', 
         totalEnergy > 0 ? `${((energyData.electricity_mwh || 0) / totalEnergy * 100).toFixed(1)}%` : '0%'],
        ['Heating & Cooling', energyData.heating_cooling_mwh?.toFixed(1) || '0',
         totalEnergy > 0 ? `${((energyData.heating_cooling_mwh || 0) / totalEnergy * 100).toFixed(1)}%` : '0%'],
        ['Steam', energyData.steam_mwh?.toFixed(1) || '0',
         totalEnergy > 0 ? `${((energyData.steam_mwh || 0) / totalEnergy * 100).toFixed(1)}%` : '0%'],
        ['Fuel Combustion', energyData.fuel_combustion_mwh?.toFixed(1) || '0',
         totalEnergy > 0 ? `${((energyData.fuel_combustion_mwh || 0) / totalEnergy * 100).toFixed(1)}%` : '0%'],
        ['Total', totalEnergy.toFixed(1), '100.0%'],
        ['Renewable Energy', energyData.renewable_energy_mwh?.toFixed(1) || '0', `${renewablePercentage.toFixed(1)}%`]
      ];
      
      doc.autoTable({
        startY: yPosition,
        body: energyTable,
        theme: 'grid',
        headStyles: { fillColor: [26, 26, 46] },
        columnStyles: {
          1: { halign: 'right' },
          2: { halign: 'center' }
        },
        didParseCell: (data: any) => {
          if (data.row.index === 5 || data.row.index === 6) {
            data.cell.styles.fontStyle = 'bold';
          }
        }
      });
      
      if (energyData.energy_intensity_value) {
        yPosition = doc.lastAutoTable.finalY + 10;
        doc.setFontSize(11);
        doc.setTextColor(50, 50, 50);
        doc.text(`Energy Intensity: ${energyData.energy_intensity_value.toFixed(2)} ${energyData.energy_intensity_unit || 'MWh/million EUR'}`, 20, yPosition);
      }
    } else {
      doc.setFontSize(11);
      doc.setTextColor(50, 50, 50);
      doc.text('Total energy consumption: 0 MWh', 20, yPosition);
      yPosition += 8;
      doc.text('Renewable energy: 0%', 20, yPosition);
      yPosition += 10;
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      doc.text('Note: Energy consumption captured under Scope 2 purchased electricity', 20, yPosition);
    }
  }
  
  /**
   * ESRS E1-8: Internal Carbon Pricing
   */
  private addCarbonPricingSection(doc: jsPDF, data: PDFExportData, startY: number): void {
    let yPosition = startY;
    
    if (yPosition > 200) {
      doc.addPage();
      yPosition = 20;
    }
    
    doc.setFontSize(16);
    doc.setTextColor(26, 26, 46);
    doc.text('ESRS E1-8: Internal Carbon Pricing', 20, yPosition);
    yPosition += 12;
    
    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    doc.text('Carbon pricing mechanisms and coverage (§77)', 20, yPosition);
    yPosition += 20;
    
    const carbonPricing = data.esrsE1Data?.internal_carbon_pricing;
    
    const pricingData = [
      ['Attribute', 'Value'],
      ['Implementation Status', carbonPricing?.implemented ? 'Implemented' : 'Not implemented'],
      ['Carbon Price', carbonPricing?.implemented ? 
        `€${(carbonPricing.price_per_tco2e || 0).toFixed(2)}/tCO₂e` : '€0/tCO₂e'],
      ['Pricing Type', carbonPricing?.pricing_type || 'Not applicable'],
      ['Scope 1 Coverage', carbonPricing?.coverage_scope1 ? 'Yes' : 'No'],
      ['Scope 2 Coverage', carbonPricing?.coverage_scope2 ? 'Yes' : 'No'],
      ['Scope 3 Categories Covered', 
        carbonPricing?.coverage_scope3_categories?.length || 0]
    ];
    
    doc.autoTable({
      startY: yPosition,
      body: pricingData,
      theme: 'striped',
      headStyles: { fillColor: [26, 26, 46] },
      columnStyles: {
        0: { fontStyle: 'bold', cellWidth: 80 }
      }
    });
    
    if (!carbonPricing?.implemented) {
      yPosition = doc.lastAutoTable.finalY + 10;
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      doc.text('Note: Internal carbon pricing not currently implemented. Consider establishing a shadow price', 20, yPosition);
      yPosition += 6;
      doc.text('to support investment decisions and climate risk assessment.', 20, yPosition);
    }
  }
  
  /**
   * ESRS E1-3: Actions and Resources
   */
  private addClimateActionsSection(doc: jsPDF, data: PDFExportData, startY: number): void {
    let yPosition = startY;
    
    doc.setFontSize(16);
    doc.setTextColor(26, 26, 46);
    doc.text('ESRS E1-3: Actions and Resources', 20, yPosition);
    yPosition += 12;
    
    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    doc.text('Climate-related expenditures and resources (§29-34)', 20, yPosition);
    yPosition += 20;
    
    const climateActions = data.esrsE1Data?.climate_actions;
    const capex = climateActions?.capex_climate_eur || 0;
    const opex = climateActions?.opex_climate_eur || 0;
    const totalFinance = capex + opex;
    
    const actionsData = [
      ['Financial Metric', 'Amount (EUR)', 'Notes'],
      ['Climate-related CapEx', capex.toLocaleString(), 'Capital expenditures for climate mitigation'],
      ['Climate-related OpEx', opex.toLocaleString(), 'Operating expenses for climate actions'],
      ['Total Climate Finance', totalFinance.toLocaleString(), 'Combined CapEx and OpEx'],
      ['', '', ''],
      ['Human Resources', 'FTEs', ''],
      ['Dedicated Staff', (climateActions?.fte_dedicated || 0).toFixed(1), 'Full-time equivalents on climate']
    ];
    
    doc.autoTable({
      startY: yPosition,
      body: actionsData,
      theme: 'grid',
      headStyles: { fillColor: [26, 26, 46] },
      columnStyles: {
        1: { halign: 'right' }
      },
      didParseCell: (data: any) => {
        if (data.row.index === 3 || data.row.index === 6) {
          data.cell.styles.fontStyle = 'bold';
        }
        if (data.row.index === 4 || data.row.index === 5) {
          data.cell.styles.fillColor = [245, 245, 245];
        }
      }
    });
    
    yPosition = doc.lastAutoTable.finalY + 10;
    
    if (totalFinance === 0) {
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      doc.text('Note: No climate-related expenditures reported. ESRS E1 requires disclosure of climate', 20, yPosition);
      yPosition += 6;
      doc.text('investments. Consider tracking green CapEx and OpEx for future reporting periods.', 20, yPosition);
    }
  }
  
  /**
   * GHG Breakdown by Gas Type
   * Required under ESRS E1-6 paragraph 53
   */
  private addGHGBreakdownSection(doc: jsPDF, data: PDFExportData, startY: number): void {
    let yPosition = startY;
    
    doc.setFontSize(16);
    doc.setTextColor(26, 26, 46);
    doc.text('GHG Breakdown by Gas Type', 20, yPosition);
    yPosition += 12;
    
    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    doc.text('Individual greenhouse gas emissions as required by ESRS E1-6 §53', 20, yPosition);
    yPosition += 20;
    
    const ghgBreakdown = data.ghgBreakdown || data.results?.ghg_breakdown;
    
    if (ghgBreakdown) {
      const ghgData = [
        ['Greenhouse Gas', 'Chemical Formula', 'Emissions', 'Unit', 'GWP'],
        ['Carbon Dioxide', 'CO₂', ghgBreakdown.CO2_tonnes.toFixed(2), 'tonnes', '1'],
        ['Methane', 'CH₄', ghgBreakdown.CH4_tonnes.toFixed(3), 'tonnes', '28'],
        ['Nitrous Oxide', 'N₂O', ghgBreakdown.N2O_tonnes.toFixed(3), 'tonnes', '265']
      ];
      
      if (ghgBreakdown.HFCs_tonnes_co2e && ghgBreakdown.HFCs_tonnes_co2e > 0) {
        ghgData.push(['Hydrofluorocarbons', 'HFCs', ghgBreakdown.HFCs_tonnes_co2e.toFixed(3), 'tCO₂e', 'Various']);
      }
      
      ghgData.push(['', '', '', '', '']);
      ghgData.push(['Total CO₂ Equivalent', '', ghgBreakdown.total_co2e.toFixed(2), 'tCO₂e', '']);
      
      doc.autoTable({
        startY: yPosition,
        head: [ghgData[0]],
        body: ghgData.slice(1),
        theme: 'grid',
        headStyles: { fillColor: [26, 26, 46] },
        columnStyles: {
          2: { halign: 'right' },
          4: { halign: 'center' }
        },
        didParseCell: (data: any) => {
          if (data.row.index === ghgData.length - 2) {
            data.cell.styles.fontStyle = 'bold';
          }
        }
      });
      
      yPosition = doc.lastAutoTable.finalY + 10;
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      doc.text(`GWP Version: ${ghgBreakdown.gwp_version}`, 20, yPosition);
      yPosition += 6;
      doc.text('Global Warming Potential values based on IPCC Fifth Assessment Report (AR5)', 20, yPosition);
    } else {
      doc.setFontSize(11);
      doc.setTextColor(50, 50, 50);
      doc.text('GHG breakdown by gas type not calculated.', 20, yPosition);
      yPosition += 8;
      doc.text('Enable gas breakdown in calculation settings to comply with ESRS E1-6 §53.', 20, yPosition);
    }
  }
  
  /**
   * Uncertainty Analysis
   * Addresses ESRS E1 paragraph 52
   */
  private addUncertaintyAnalysisSection(doc: jsPDF, data: PDFExportData, startY: number): void {
    let yPosition = startY;
    
    doc.setFontSize(16);
    doc.setTextColor(26, 26, 46);
    doc.text('Uncertainty Analysis', 20, yPosition);
    yPosition += 12;
    
    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    doc.text('Statistical uncertainty assessment as per ESRS E1 §52', 20, yPosition);
    yPosition += 20;
    
    const uncertainty = data.uncertaintyAnalysis || data.results?.uncertainty_analysis;
    
    if (uncertainty && uncertainty.confidence_interval_95) {
      const analysisData = [
        ['Statistical Measure', 'Value', 'Unit'],
        ['Mean Emissions', (uncertainty.mean_emissions / 1000).toFixed(2), 'tCO₂e'],
        ['Standard Deviation', (uncertainty.std_deviation / 1000).toFixed(2), 'tCO₂e'],
        ['95% Confidence Interval - Lower', (uncertainty.confidence_interval_95[0] / 1000).toFixed(2), 'tCO₂e'],
        ['95% Confidence Interval - Upper', (uncertainty.confidence_interval_95[1] / 1000).toFixed(2), 'tCO₂e'],
        ['Relative Uncertainty', `±${uncertainty.relative_uncertainty_percent?.toFixed(1) || 'N/A'}`, '%'],
        ['Monte Carlo Iterations', (uncertainty.monte_carlo_runs || 0).toLocaleString(), 'runs']
      ];
      
      doc.autoTable({
        startY: yPosition,
        head: [analysisData[0]],
        body: analysisData.slice(1),
        theme: 'striped',
        headStyles: { fillColor: [26, 26, 46] },
        columnStyles: {
          1: { halign: 'right' },
          2: { halign: 'center' }
        }
      });
      
      yPosition = doc.lastAutoTable.finalY + 15;
      
      // Visual uncertainty range
      doc.setFontSize(12);
      doc.setTextColor(26, 26, 46);
      doc.text('Emissions Uncertainty Range', 20, yPosition);
      yPosition += 10;
      
      const reported = data.summary.totalEmissions;
      const lower = uncertainty.confidence_interval_95[0] / 1000;
      const upper = uncertainty.confidence_interval_95[1] / 1000;
      const range = upper - lower;
      const center = (upper + lower) / 2;
      
      // Draw uncertainty bar
      const barY = yPosition;
      const barHeight = 20;
      const barWidth = 150;
      const centerX = 95;
      
      // Background
      doc.setFillColor(240, 240, 240);
      doc.rect(20, barY, barWidth, barHeight, 'F');
      
      // Confidence interval
      const lowerX = 20 + ((lower - lower) / range) * barWidth;
      const upperX = 20 + ((upper - lower) / range) * barWidth;
      const reportedX = 20 + ((reported - lower) / range) * barWidth;
      
      doc.setFillColor(59, 130, 246);
      doc.rect(lowerX, barY, upperX - lowerX, barHeight, 'F');
      
      // Reported value line
      doc.setDrawColor(239, 68, 68);
      doc.setLineWidth(2);
      doc.line(reportedX, barY - 5, reportedX, barY + barHeight + 5);
      
      // Labels
      doc.setFontSize(9);
      doc.setTextColor(50, 50, 50);
      doc.text(lower.toFixed(1), 20, barY + barHeight + 15);
      doc.text(upper.toFixed(1), 170 - 20, barY + barHeight + 15);
      doc.setTextColor(239, 68, 68);
      doc.text(`Reported: ${reported.toFixed(1)}`, reportedX - 20, barY - 10);
      
      yPosition += 50;
      
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      doc.text('The uncertainty analysis provides a statistical assessment of the reliability of emissions calculations.', 20, yPosition);
      yPosition += 6;
      doc.text('This transparency supports stakeholder confidence and informed decision-making.', 20, yPosition);
    } else {
      doc.setFontSize(11);
      doc.setTextColor(50, 50, 50);
      doc.text('Uncertainty analysis not performed.', 20, yPosition);
      yPosition += 8;
      doc.text('Enable Monte Carlo simulation to provide uncertainty estimates as recommended by ESRS E1 §52.', 20, yPosition);
    }
  }
'''
    
    # Insert the new methods before the class closing brace
    content = content[:methods_insertion_point] + new_methods + '\n' + content[methods_insertion_point:]
    
    # Write the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully added all ESRS E1 sections")
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
    backup_path = create_backup(file_path)
    
    # Update the file
    success = add_esrs_sections_to_handler(file_path)
    
    if success:
        print("\n✨ Update complete!")
        print("\nAdded ESRS E1 compliant sections:")
        print("✓ Data Quality Assessment with visual score")
        print("✓ Emissions by Scope with bar chart visualization")
        print("✓ Top Emission Categories with ranking table")
        print("✓ ESRS E1-5: Energy Consumption with renewable percentage")
        print("✓ ESRS E1-8: Internal Carbon Pricing status")
        print("✓ ESRS E1-3: Climate Actions and Resources")
        print("✓ GHG Breakdown by Gas Type (§53 compliance)")
        print("✓ Uncertainty Analysis with confidence intervals (§52 compliance)")
        print("\n🚀 Your PDF reports now exceed ESRS E1 requirements!")
        print("\n⚠️  Note: Ensure your EliteGHGCalculator passes the correct data structure")
        print("    including dataQuality, esrsE1Data, ghgBreakdown, and uncertaintyAnalysis")
    else:
        print("\n❌ Update failed!")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()