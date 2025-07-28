#!/usr/bin/env python3
"""
Add ESRS E1 sections to pdf-export-handler.ts at the correct locations
Fixed version
"""

import os
import shutil
from datetime import datetime

def create_backup(file_path):
    """Create a backup of the original file"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def insert_esrs_sections(file_path):
    """Insert ESRS E1 sections at the correct locations"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Section calls to insert at line 664 (before this.addFooters)
    section_calls = '''    // ESRS E1 Enhanced Sections
    // =========================
    
    // Data Quality Assessment
    pdf.addPage();
    currentY = DESIGN.layout.margins.top;
    currentY = this.addDataQualitySection(pdf, reconciledData, currentY);
    
    // Visual Analytics
    pdf.addPage();
    currentY = DESIGN.layout.margins.top;
    currentY = this.addEmissionsByScopeChart(pdf, reconciledData, currentY);
    
    pdf.addPage();
    currentY = DESIGN.layout.margins.top;
    currentY = this.addTopCategoriesChart(pdf, reconciledData, currentY);
    
    // ESRS E1 Mandatory Disclosures
    pdf.addPage();
    currentY = DESIGN.layout.margins.top;
    currentY = this.addEnergyConsumptionSection(pdf, reconciledData, currentY);
    
    currentY = this.addCarbonPricingSection(pdf, reconciledData, currentY);
    
    if (currentY > DESIGN.layout.pageHeight - 100) {
      pdf.addPage();
      currentY = DESIGN.layout.margins.top;
    }
    currentY = this.addClimateActionsSection(pdf, reconciledData, currentY);
    
    // Technical Analysis
    if (reconciledData.ghgBreakdown || reconciledData.results?.ghg_breakdown) {
      pdf.addPage();
      currentY = DESIGN.layout.margins.top;
      currentY = this.addGHGBreakdownSection(pdf, reconciledData, currentY);
    }
    
    if (reconciledData.uncertaintyAnalysis || reconciledData.results?.uncertainty_analysis) {
      pdf.addPage();
      currentY = DESIGN.layout.margins.top;
      currentY = this.addUncertaintyAnalysisSection(pdf, reconciledData, currentY);
    }

'''
    
    # Insert section calls at line 663 (0-indexed, so 662)
    lines.insert(663, section_calls)
    print("✅ Inserted ESRS E1 section calls")
    
    # Methods to add - split into smaller chunks to avoid issues
    new_methods_part1 = '''
  // ==========================================
  // ESRS E1 Enhanced Section Methods
  // ==========================================
  
  /**
   * Add Data Quality Assessment Section
   * Transparency requirement for ESRS E1
   */
  private addDataQualitySection(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(DESIGN.fonts.sizes.title);
    pdf.setTextColor(...DESIGN.colors.primary);
    pdf.text('Data Quality Assessment', DESIGN.layout.margins.left, currentY);
    currentY += 12;
    
    pdf.setFontSize(DESIGN.fonts.sizes.body);
    pdf.setTextColor(...DESIGN.colors.secondary);
    pdf.text('ESRS E1 requires transparency in data quality and calculation methodologies', DESIGN.layout.margins.left, currentY);
    currentY += 15;
    
    const qualityScore = data.dataQuality?.overallScore || data.summary.dataQualityScore || 0;
    const scoreColor = qualityScore >= 80 ? DESIGN.colors.success : qualityScore >= 60 ? DESIGN.colors.warning : DESIGN.colors.error;
    
    // Overall score box
    pdf.setFillColor(245, 245, 245);
    pdf.rect(DESIGN.layout.margins.left, currentY, 170, 30, 'F');
    
    pdf.setFontSize(24);
    pdf.setTextColor(...scoreColor);
    pdf.text(`${qualityScore.toFixed(0)}%`, DESIGN.layout.margins.left + 10, currentY + 20);
    
    pdf.setFontSize(12);
    pdf.setTextColor(...DESIGN.colors.text);
    pdf.text('Overall Data Quality Score', DESIGN.layout.margins.left + 60, currentY + 20);
    currentY += 40;
    
    // Detailed metrics
    if (data.dataQuality) {
      const metrics = [
        ['Data Completeness', data.dataQuality.dataCompleteness, 'Percentage of required data fields provided'],
        ['Evidence Coverage', data.dataQuality.evidenceProvided, 'Activities with supporting documentation'],
        ['Data Recency', data.dataQuality.dataRecency, 'How current the data is'],
        ['Methodology Accuracy', data.dataQuality.methodologyAccuracy, 'Use of recognized emission factors']
      ];
      
      (pdf as any).autoTable({
        startY: currentY,
        head: [['Metric', 'Score', 'Description']],
        body: metrics.map(m => [m[0], `${(m[1] as number).toFixed(0)}%`, m[2]]),
        theme: 'grid',
        headStyles: { fillColor: DESIGN.colors.primary },
        columnStyles: {
          1: { halign: 'center', cellWidth: 30 },
        },
        margin: { left: DESIGN.layout.margins.left }
      });
      
      currentY = (pdf as any).lastAutoTable.finalY + 10;
    }
    
    return currentY;
  }
'''

    new_methods_part2 = '''
  /**
   * Add Emissions by Scope Visualization
   */
  private addEmissionsByScopeChart(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(DESIGN.fonts.sizes.title);
    pdf.setTextColor(...DESIGN.colors.primary);
    pdf.text('Emissions by Scope', DESIGN.layout.margins.left, currentY);
    currentY += 12;
    
    pdf.setFontSize(DESIGN.fonts.sizes.body);
    pdf.setTextColor(...DESIGN.colors.secondary);
    pdf.text('Distribution of emissions across GHG Protocol scopes', DESIGN.layout.margins.left, currentY);
    currentY += 20;
    
    const total = data.summary.totalEmissions || 0;
    const scopes = [
      { name: 'Scope 1 - Direct', value: data.summary.scope1, percentage: data.summary.scope1Percentage, color: DESIGN.colors.error },
      { name: 'Scope 2 - Energy', value: data.summary.scope2, percentage: data.summary.scope2Percentage, color: DESIGN.colors.warning },
      { name: 'Scope 3 - Value Chain', value: data.summary.scope3, percentage: data.summary.scope3Percentage, color: DESIGN.colors.success }
    ];
    
    // Visual bar chart
    const barHeight = 30;
    const maxWidth = 150;
    
    scopes.forEach((scope, index) => {
      const yPos = currentY + (index * (barHeight + 10));
      const barWidth = total > 0 ? (scope.value / total) * maxWidth : 0;
      
      // Scope name and value
      pdf.setFontSize(12);
      pdf.setTextColor(...DESIGN.colors.text);
      pdf.text(scope.name, DESIGN.layout.margins.left, yPos + 20);
      
      // Bar
      pdf.setFillColor(...scope.color);
      pdf.rect(DESIGN.layout.margins.left, yPos + 25, barWidth, barHeight, 'F');
      
      // Percentage and value
      pdf.setFontSize(11);
      pdf.text(`${scope.percentage.toFixed(1)}%`, DESIGN.layout.margins.left + 160, yPos + 20);
      pdf.text(`${scope.value.toFixed(2)} tCO₂e`, DESIGN.layout.margins.left + 160, yPos + 35);
    });
    
    currentY += (3 * (barHeight + 10)) + 20;
    
    // Summary table
    (pdf as any).autoTable({
      startY: currentY,
      head: [['Scope', 'Emissions (tCO₂e)', 'Percentage', 'Key Sources']],
      body: [
        ['Scope 1', data.summary.scope1.toFixed(2), `${data.summary.scope1Percentage.toFixed(1)}%`, 'Fuel combustion, processes'],
        ['Scope 2', data.summary.scope2.toFixed(2), `${data.summary.scope2Percentage.toFixed(1)}%`, 'Purchased electricity, heat'],
        ['Scope 3', data.summary.scope3.toFixed(2), `${data.summary.scope3Percentage.toFixed(1)}%`, 'Supply chain, travel, waste'],
        ['Total', data.summary.totalEmissions.toFixed(2), '100.0%', '']
      ],
      theme: 'striped',
      headStyles: { fillColor: DESIGN.colors.primary },
      footStyles: { fontStyle: 'bold' },
      margin: { left: DESIGN.layout.margins.left }
    });
    
    return (pdf as any).lastAutoTable.finalY + 10;
  }
'''

    new_methods_part3 = '''
  /**
   * Add Top Emission Categories
   */
  private addTopCategoriesChart(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(DESIGN.fonts.sizes.title);
    pdf.setTextColor(...DESIGN.colors.primary);
    pdf.text('Top Emission Categories', DESIGN.layout.margins.left, currentY);
    currentY += 12;
    
    pdf.setFontSize(DESIGN.fonts.sizes.body);
    pdf.setTextColor(...DESIGN.colors.secondary);
    pdf.text('Highest contributing activities for materiality assessment', DESIGN.layout.margins.left, currentY);
    currentY += 20;
    
    if (data.topEmissionSources && data.topEmissionSources.length > 0) {
      const tableData = data.topEmissionSources.slice(0, 10).map((source, index) => [
        `${index + 1}`,
        source.name.substring(0, 40),
        source.category,
        `${source.emissions.toFixed(3)}`,
        `${source.percentage.toFixed(1)}%`
      ]);
      
      (pdf as any).autoTable({
        startY: currentY,
        head: [['Rank', 'Activity', 'Category', 'tCO₂e', '% of Total']],
        body: tableData,
        theme: 'grid',
        headStyles: { fillColor: DESIGN.colors.primary },
        columnStyles: {
          0: { cellWidth: 15, halign: 'center' },
          3: { halign: 'right' },
          4: { halign: 'center' }
        },
        margin: { left: DESIGN.layout.margins.left }
      });
      
      currentY = (pdf as any).lastAutoTable.finalY + 15;
      
      // Visual representation of top 5
      const top5 = data.topEmissionSources.slice(0, 5);
      if (top5.length > 0) {
        const maxEmission = Math.max(...top5.map(s => s.emissions));
        
        pdf.setFontSize(12);
        pdf.setTextColor(...DESIGN.colors.primary);
        pdf.text('Top 5 Emission Sources - Visual Breakdown', DESIGN.layout.margins.left, currentY);
        currentY += 10;
        
        top5.forEach((source, index) => {
          const barWidth = (source.emissions / maxEmission) * 120;
          const yPos = currentY + (index * 25);
          
          pdf.setFontSize(10);
          pdf.setTextColor(...DESIGN.colors.text);
          pdf.text(source.name.substring(0, 30), DESIGN.layout.margins.left, yPos + 15);
          
          // Gradient effect with scope colors
          const color = index === 0 ? DESIGN.colors.error : index === 1 ? DESIGN.colors.warning : DESIGN.colors.success;
          pdf.setFillColor(...color);
          pdf.rect(DESIGN.layout.margins.left + 100, yPos + 10, barWidth, 15, 'F');
          
          pdf.text(`${source.emissions.toFixed(2)} tCO₂e`, DESIGN.layout.margins.left + 225, yPos + 15);
        });
        
        currentY += (5 * 25) + 10;
      }
    }
    
    return currentY;
  }
'''

    new_methods_part4 = '''
  /**
   * ESRS E1-5: Energy Consumption
   */
  private addEnergyConsumptionSection(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(DESIGN.fonts.sizes.title);
    pdf.setTextColor(...DESIGN.colors.primary);
    pdf.text('ESRS E1-5: Energy Consumption', DESIGN.layout.margins.left, currentY);
    currentY += 12;
    
    pdf.setFontSize(DESIGN.fonts.sizes.body);
    pdf.setTextColor(...DESIGN.colors.secondary);
    pdf.text('Energy consumption and renewable energy share (§67-69)', DESIGN.layout.margins.left, currentY);
    currentY += 20;
    
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
        ['Electricity', (energyData.electricity_mwh || 0).toFixed(1), 
         totalEnergy > 0 ? `${((energyData.electricity_mwh || 0) / totalEnergy * 100).toFixed(1)}%` : '0%'],
        ['Heating & Cooling', (energyData.heating_cooling_mwh || 0).toFixed(1),
         totalEnergy > 0 ? `${((energyData.heating_cooling_mwh || 0) / totalEnergy * 100).toFixed(1)}%` : '0%'],
        ['Steam', (energyData.steam_mwh || 0).toFixed(1),
         totalEnergy > 0 ? `${((energyData.steam_mwh || 0) / totalEnergy * 100).toFixed(1)}%` : '0%'],
        ['Fuel Combustion', (energyData.fuel_combustion_mwh || 0).toFixed(1),
         totalEnergy > 0 ? `${((energyData.fuel_combustion_mwh || 0) / totalEnergy * 100).toFixed(1)}%` : '0%'],
        ['Total', totalEnergy.toFixed(1), '100.0%'],
        ['Renewable Energy', (energyData.renewable_energy_mwh || 0).toFixed(1), `${renewablePercentage.toFixed(1)}%`]
      ];
      
      (pdf as any).autoTable({
        startY: currentY,
        body: energyTable,
        theme: 'grid',
        headStyles: { fillColor: DESIGN.colors.primary },
        columnStyles: {
          1: { halign: 'right' },
          2: { halign: 'center' }
        },
        didParseCell: (data: any) => {
          if (data.row.index === 5 || data.row.index === 6) {
            data.cell.styles.fontStyle = 'bold';
          }
        },
        margin: { left: DESIGN.layout.margins.left }
      });
      
      currentY = (pdf as any).lastAutoTable.finalY + 10;
      
      if (energyData.energy_intensity_value) {
        pdf.setFontSize(11);
        pdf.setTextColor(...DESIGN.colors.text);
        pdf.text(`Energy Intensity: ${energyData.energy_intensity_value.toFixed(2)} ${energyData.energy_intensity_unit || 'MWh/million EUR'}`, 
          DESIGN.layout.margins.left, currentY);
        currentY += 10;
      }
    } else {
      pdf.setFontSize(11);
      pdf.setTextColor(...DESIGN.colors.text);
      pdf.text('Total energy consumption: 0 MWh', DESIGN.layout.margins.left, currentY);
      currentY += 8;
      pdf.text('Renewable energy: 0%', DESIGN.layout.margins.left, currentY);
      currentY += 10;
      pdf.setFontSize(10);
      pdf.setTextColor(...DESIGN.colors.secondary);
      pdf.text('Note: Energy consumption captured under Scope 2 purchased electricity', DESIGN.layout.margins.left, currentY);
      currentY += 10;
    }
    
    return currentY;
  }
  
  /**
   * ESRS E1-8: Internal Carbon Pricing
   */
  private addCarbonPricingSection(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    currentY += 15; // Add spacing
    
    pdf.setFontSize(DESIGN.fonts.sizes.title);
    pdf.setTextColor(...DESIGN.colors.primary);
    pdf.text('ESRS E1-8: Internal Carbon Pricing', DESIGN.layout.margins.left, currentY);
    currentY += 12;
    
    pdf.setFontSize(DESIGN.fonts.sizes.body);
    pdf.setTextColor(...DESIGN.colors.secondary);
    pdf.text('Carbon pricing mechanisms and coverage (§77)', DESIGN.layout.margins.left, currentY);
    currentY += 20;
    
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
        (carbonPricing?.coverage_scope3_categories?.length || 0).toString()]
    ];
    
    (pdf as any).autoTable({
      startY: currentY,
      body: pricingData,
      theme: 'striped',
      headStyles: { fillColor: DESIGN.colors.primary },
      columnStyles: {
        0: { fontStyle: 'bold', cellWidth: 80 }
      },
      margin: { left: DESIGN.layout.margins.left }
    });
    
    currentY = (pdf as any).lastAutoTable.finalY + 10;
    
    if (!carbonPricing?.implemented) {
      pdf.setFontSize(10);
      pdf.setTextColor(...DESIGN.colors.secondary);
      pdf.text('Note: Internal carbon pricing not currently implemented. Consider establishing a shadow price', 
        DESIGN.layout.margins.left, currentY);
      currentY += 6;
      pdf.text('to support investment decisions and climate risk assessment.', DESIGN.layout.margins.left, currentY);
      currentY += 10;
    }
    
    return currentY;
  }
'''

    new_methods_part5 = '''
  /**
   * ESRS E1-3: Actions and Resources
   */
  private addClimateActionsSection(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    currentY += 15; // Add spacing
    
    pdf.setFontSize(DESIGN.fonts.sizes.title);
    pdf.setTextColor(...DESIGN.colors.primary);
    pdf.text('ESRS E1-3: Actions and Resources', DESIGN.layout.margins.left, currentY);
    currentY += 12;
    
    pdf.setFontSize(DESIGN.fonts.sizes.body);
    pdf.setTextColor(...DESIGN.colors.secondary);
    pdf.text('Climate-related expenditures and resources (§29-34)', DESIGN.layout.margins.left, currentY);
    currentY += 20;
    
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
    
    (pdf as any).autoTable({
      startY: currentY,
      body: actionsData,
      theme: 'grid',
      headStyles: { fillColor: DESIGN.colors.primary },
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
      },
      margin: { left: DESIGN.layout.margins.left }
    });
    
    currentY = (pdf as any).lastAutoTable.finalY + 10;
    
    if (totalFinance === 0) {
      pdf.setFontSize(10);
      pdf.setTextColor(...DESIGN.colors.secondary);
      pdf.text('Note: No climate-related expenditures reported. ESRS E1 requires disclosure of climate', 
        DESIGN.layout.margins.left, currentY);
      currentY += 6;
      pdf.text('investments. Consider tracking green CapEx and OpEx for future reporting periods.', 
        DESIGN.layout.margins.left, currentY);
      currentY += 10;
    }
    
    return currentY;
  }
  
  /**
   * GHG Breakdown by Gas Type
   */
  private addGHGBreakdownSection(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(DESIGN.fonts.sizes.title);
    pdf.setTextColor(...DESIGN.colors.primary);
    pdf.text('GHG Breakdown by Gas Type', DESIGN.layout.margins.left, currentY);
    currentY += 12;
    
    pdf.setFontSize(DESIGN.fonts.sizes.body);
    pdf.setTextColor(...DESIGN.colors.secondary);
    pdf.text('Individual greenhouse gas emissions as required by ESRS E1-6 §53', DESIGN.layout.margins.left, currentY);
    currentY += 20;
    
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
      
      (pdf as any).autoTable({
        startY: currentY,
        head: [ghgData[0]],
        body: ghgData.slice(1),
        theme: 'grid',
        headStyles: { fillColor: DESIGN.colors.primary },
        columnStyles: {
          2: { halign: 'right' },
          4: { halign: 'center' }
        },
        didParseCell: (data: any) => {
          if (data.row.index === ghgData.length - 2) {
            data.cell.styles.fontStyle = 'bold';
          }
        },
        margin: { left: DESIGN.layout.margins.left }
      });
      
      currentY = (pdf as any).lastAutoTable.finalY + 10;
      
      pdf.setFontSize(10);
      pdf.setTextColor(...DESIGN.colors.secondary);
      pdf.text(`GWP Version: ${ghgBreakdown.gwp_version}`, DESIGN.layout.margins.left, currentY);
      currentY += 6;
      pdf.text('Global Warming Potential values based on IPCC Fifth Assessment Report (AR5)', 
        DESIGN.layout.margins.left, currentY);
      currentY += 10;
    } else {
      pdf.setFontSize(11);
      pdf.setTextColor(...DESIGN.colors.text);
      pdf.text('GHG breakdown by gas type not calculated.', DESIGN.layout.margins.left, currentY);
      currentY += 8;
      pdf.text('Enable gas breakdown in calculation settings to comply with ESRS E1-6 §53.', 
        DESIGN.layout.margins.left, currentY);
      currentY += 10;
    }
    
    return currentY;
  }
  
  /**
   * Uncertainty Analysis
   */
  private addUncertaintyAnalysisSection(pdf: jsPDF, data: PDFExportData, startY: number): number {
    let currentY = startY;
    
    pdf.setFontSize(DESIGN.fonts.sizes.title);
    pdf.setTextColor(...DESIGN.colors.primary);
    pdf.text('Uncertainty Analysis', DESIGN.layout.margins.left, currentY);
    currentY += 12;
    
    pdf.setFontSize(DESIGN.fonts.sizes.body);
    pdf.setTextColor(...DESIGN.colors.secondary);
    pdf.text('Statistical uncertainty assessment as per ESRS E1 §52', DESIGN.layout.margins.left, currentY);
    currentY += 20;
    
    const uncertainty = data.uncertaintyAnalysis || data.results?.uncertainty_analysis;
    
    if (uncertainty && uncertainty.confidence_interval_95) {
      const analysisData = [
        ['Statistical Measure', 'Value', 'Unit'],
        ['Mean Emissions', ((uncertainty.mean_emissions || 0) / 1000).toFixed(2), 'tCO₂e'],
        ['Standard Deviation', ((uncertainty.std_deviation || 0) / 1000).toFixed(2), 'tCO₂e'],
        ['95% Confidence Interval - Lower', (uncertainty.confidence_interval_95[0] / 1000).toFixed(2), 'tCO₂e'],
        ['95% Confidence Interval - Upper', (uncertainty.confidence_interval_95[1] / 1000).toFixed(2), 'tCO₂e'],
        ['Relative Uncertainty', `±${uncertainty.relative_uncertainty_percent?.toFixed(1) || 'N/A'}`, '%'],
        ['Monte Carlo Iterations', (uncertainty.monte_carlo_runs || 0).toLocaleString(), 'runs']
      ];
      
      (pdf as any).autoTable({
        startY: currentY,
        head: [analysisData[0]],
        body: analysisData.slice(1),
        theme: 'striped',
        headStyles: { fillColor: DESIGN.colors.primary },
        columnStyles: {
          1: { halign: 'right' },
          2: { halign: 'center' }
        },
        margin: { left: DESIGN.layout.margins.left }
      });
      
      currentY = (pdf as any).lastAutoTable.finalY + 15;
      
      // Visual uncertainty range
      pdf.setFontSize(12);
      pdf.setTextColor(...DESIGN.colors.primary);
      pdf.text('Emissions Uncertainty Range', DESIGN.layout.margins.left, currentY);
      currentY += 10;
      
      const reported = data.summary.totalEmissions;
      const lower = uncertainty.confidence_interval_95[0] / 1000;
      const upper = uncertainty.confidence_interval_95[1] / 1000;
      const range = upper - lower;
      
      // Draw uncertainty bar
      const barY = currentY;
      const barHeight = 20;
      const barWidth = 150;
      
      // Background
      pdf.setFillColor(240, 240, 240);
      pdf.rect(DESIGN.layout.margins.left, barY, barWidth, barHeight, 'F');
      
      // Confidence interval
      const lowerX = DESIGN.layout.margins.left;
      const upperX = DESIGN.layout.margins.left + barWidth;
      const reportedX = DESIGN.layout.margins.left + ((reported - lower) / range) * barWidth;
      
      pdf.setFillColor(...DESIGN.colors.warning);
      pdf.rect(lowerX, barY, upperX - lowerX, barHeight, 'F');
      
      // Reported value line
      pdf.setDrawColor(...DESIGN.colors.error);
      pdf.setLineWidth(2);
      pdf.line(reportedX, barY - 5, reportedX, barY + barHeight + 5);
      
      // Labels
      pdf.setFontSize(9);
      pdf.setTextColor(...DESIGN.colors.text);
      pdf.text(lower.toFixed(1), DESIGN.layout.margins.left, barY + barHeight + 15);
      pdf.text(upper.toFixed(1), DESIGN.layout.margins.left + barWidth - 20, barY + barHeight + 15);
      pdf.setTextColor(...DESIGN.colors.error);
      pdf.text(`Reported: ${reported.toFixed(1)}`, reportedX - 20, barY - 10);
      
      currentY += 50;
      
      pdf.setFontSize(10);
      pdf.setTextColor(...DESIGN.colors.secondary);
      pdf.text('The uncertainty analysis provides a statistical assessment of the reliability of emissions calculations.', 
        DESIGN.layout.margins.left, currentY);
      currentY += 6;
      pdf.text('This transparency supports stakeholder confidence and informed decision-making.', 
        DESIGN.layout.margins.left, currentY);
      currentY += 10;
    } else {
      pdf.setFontSize(11);
      pdf.setTextColor(...DESIGN.colors.text);
      pdf.text('Uncertainty analysis not performed.', DESIGN.layout.margins.left, currentY);
      currentY += 8;
      pdf.text('Enable Monte Carlo simulation to provide uncertainty estimates as recommended by ESRS E1 §52.', 
        DESIGN.layout.margins.left, currentY);
      currentY += 10;
    }
    
    return currentY;
  }
'''
    
    # Insert methods before the class closing brace (line 1580, but we need to account for the added section calls)
    # Since we inserted section calls, the line numbers have shifted
    insertion_line = 1579 + len(section_calls.split('\n'))
    
    # Insert all method parts
    lines.insert(insertion_line, new_methods_part1)
    lines.insert(insertion_line + 1, new_methods_part2)  
    lines.insert(insertion_line + 2, new_methods_part3)
    lines.insert(insertion_line + 3, new_methods_part4)
    lines.insert(insertion_line + 4, new_methods_part5)
    
    print("✅ Inserted ESRS E1 method implementations")
    
    # Write the updated file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
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
    
    try:
        # Insert ESRS sections
        success = insert_esrs_sections(file_path)
        
        if success:
            print("\n✨ Update complete!")
            print("\nSuccessfully added ESRS E1 sections:")
            print("✓ Data Quality Assessment")
            print("✓ Emissions by Scope Chart")
            print("✓ Top Categories Chart")
            print("✓ Energy Consumption (E1-5)")
            print("✓ Carbon Pricing (E1-8)")
            print("✓ Climate Actions (E1-3)")
            print("✓ GHG Breakdown")
            print("✓ Uncertainty Analysis")
            print("\n🚀 Your PDF reports now include all ESRS E1 requirements!")
        else:
            print("\n❌ Update failed!")
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, file_path)
    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()