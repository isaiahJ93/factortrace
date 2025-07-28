#!/usr/bin/env python3
"""
Update EliteGHGCalculator.tsx with fixed preparePDFExportData function
Run from: /Users/isaiah/Documents/Scope3Tool
"""

import re
import os
import shutil
from datetime import datetime
import sys

def create_backup(file_path):
    """Create a backup of the original file"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def update_prepare_pdf_export_data(file_path):
    """Update the preparePDFExportData function in the file"""
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The new function to replace with
    new_function = '''  // FIXED: Prepare comprehensive PDF export data
  const preparePDFExportData = () => {
    if (!results) return null;
    
    console.log('DEBUG - API Results:', results); // Debug log
    
    // Helper function to safely parse numbers
    const safeParseNumber = (value: any): number => {
      if (typeof value === 'number') return value;
      if (typeof value === 'string') return parseFloat(value) || 0;
      return 0;
    };
    
    // Helper function to calculate scope totals from activities
    const calculateScopeFromActivities = (scopeId: string): number => {
      return activities
        .filter(a => a.scopeId === scopeId)
        .reduce((sum, activity) => {
          const amount = safeParseNumber(activity.amount);
          const factor = safeParseNumber(activity.factor);
          return sum + (amount * factor) / 1000; // Convert kg to tons
        }, 0);
    };
    
    // Extract values from API response - handle all possible field names
    const apiSummary = results.summary || {};
    
    // Total emissions - check multiple possible field names
    const totalFromAPI = apiSummary.totalEmissions || 
                        apiSummary.total_emissions_tons_co2e || 
                        apiSummary.total_emissions ||
                        apiSummary.totalCO2e || 0;
    
    // Scope 1 - check all variations
    const scope1FromAPI = apiSummary.scope1 || 
                         apiSummary.scope1_emissions || 
                         apiSummary.scope1_total ||
                         apiSummary.scope1Emissions || 0;
    
    // Scope 2 - check all variations INCLUDING location/market based
    const scope2LocationFromAPI = apiSummary.scope2 || 
                                 apiSummary.scope2_emissions ||
                                 apiSummary.scope2_location_based || 
                                 apiSummary.scope2_location ||
                                 apiSummary.scope2LocationBased ||
                                 apiSummary.scope2_total || 0;
    
    const scope2MarketFromAPI = apiSummary.scope2_market_based || 
                               apiSummary.scope2_market ||
                               apiSummary.scope2Market ||
                               apiSummary.scope2MarketBased || 
                               scope2LocationFromAPI; // Default to location-based
    
    // Scope 3 - check all variations
    const scope3FromAPI = apiSummary.scope3 || 
                         apiSummary.scope3_emissions || 
                         apiSummary.scope3_total ||
                         apiSummary.scope3Emissions || 0;
    
    // Determine if values are in kg or tons
    // If total is much smaller than sum of scopes, scopes are likely in kg
    const sumOfScopes = scope1FromAPI + scope2LocationFromAPI + scope3FromAPI;
    const needsConversion = totalFromAPI > 0 && sumOfScopes > totalFromAPI * 100;
    
    // Convert to tons with intelligent detection
    let scope1InTons, scope2InTons, scope2MarketInTons, scope3InTons;
    
    if (needsConversion || sumOfScopes > 100) {
      // Values are likely in kg, convert to tons
      scope1InTons = scope1FromAPI / 1000;
      scope2InTons = scope2LocationFromAPI / 1000;
      scope2MarketInTons = scope2MarketFromAPI / 1000;
      scope3InTons = scope3FromAPI / 1000;
    } else {
      // Values might already be in tons, but verify
      scope1InTons = scope1FromAPI;
      scope2InTons = scope2LocationFromAPI;
      scope2MarketInTons = scope2MarketFromAPI;
      scope3InTons = scope3FromAPI;
    }
    
    // Calculate from activities as backup
    const scope1Calculated = calculateScopeFromActivities('scope1');
    const scope2Calculated = calculateScopeFromActivities('scope2');
    const scope3Calculated = calculateScopeFromActivities('scope3');
    
    // Use calculated values if API values seem wrong (e.g., scope2 is 0 but we have activities)
    if (scope2InTons === 0 && scope2Calculated > 0) {
      console.warn('Using calculated Scope 2 value as API returned 0');
      scope2InTons = scope2Calculated;
    }
    
    // Reconcile totals
    const calculatedTotal = scope1InTons + scope2InTons + scope3InTons;
    const totalEmissions = calculatedTotal; // Use calculated total for consistency
    
    // Calculate percentages
    const scope1Percentage = totalEmissions > 0 ? (scope1InTons / totalEmissions) * 100 : 0;
    const scope2Percentage = totalEmissions > 0 ? (scope2InTons / totalEmissions) * 100 : 0;
    const scope3Percentage = totalEmissions > 0 ? (scope3InTons / totalEmissions) * 100 : 0;
    
    console.log('DEBUG - Calculated values:', {
      scope1InTons,
      scope2InTons,
      scope3InTons,
      totalEmissions,
      percentages: { scope1: scope1Percentage, scope2: scope2Percentage, scope3: scope3Percentage }
    });
    
    // Process breakdown/activities
    const breakdown = results.enhancedBreakdown || results.breakdown || [];
    
    // Identify top emission sources from activities
    const allActivities = [...activities, ...breakdown].filter(Boolean);
    const topEmissionSources = allActivities
      .map(item => {
        const amount = safeParseNumber(item.amount);
        const factor = safeParseNumber(item.factor);
        const emissions = item.emissions_tons || 
                         item.emissions || 
                         (amount * factor / 1000) || 0;
        
        return {
          name: item.name || item.activity || item.category || 'Unknown',
          category: item.categoryName || item.category || item.scope || 'Unknown',
          emissions: emissions,
          percentage: totalEmissions > 0 ? (emissions / totalEmissions) * 100 : 0
        };
      })
      .filter(item => item.emissions > 0)
      .sort((a, b) => b.emissions - a.emissions)
      .slice(0, 5);
    
    // Prepare scope 3 category analysis
    const scope3Categories = {};
    
    // Process activities to build scope 3 analysis
    activities
      .filter(a => a.scopeId === 'scope3')
      .forEach(activity => {
        const categoryName = activity.categoryName || 'Other';
        if (!scope3Categories[categoryName]) {
          scope3Categories[categoryName] = {
            category: categoryName,
            emissions: 0,
            activities: 0,
            hasEvidence: false
          };
        }
        
        const amount = safeParseNumber(activity.amount);
        const factor = safeParseNumber(activity.factor);
        const emissions = (amount * factor) / 1000;
        
        scope3Categories[categoryName].emissions += emissions;
        scope3Categories[categoryName].activities += 1;
        scope3Categories[categoryName].hasEvidence = 
          scope3Categories[categoryName].hasEvidence || 
          (activity.evidence && activity.evidence.length > 0);
      });
    
    const scope3Analysis = Object.values(scope3Categories).map((cat: any) => ({
      ...cat,
      percentage: scope3InTons > 0 ? (cat.emissions / scope3InTons) * 100 : 0
    }));
    
    // Build final PDF data structure
    const pdfData = {
      metadata: {
        reportTitle: 'GHG Emissions Report',
        companyName: companyName || 'Company',
        reportingPeriod: reportingPeriod || new Date().getFullYear().toString(),
        generatedDate: new Date().toISOString(),
        documentId: `GHG-${Date.now().toString(36).toUpperCase()}`,
        standard: 'ESRS E1 Compliant',
        methodology: 'GHG Protocol Corporate Standard'
      },
      summary: {
        totalEmissions: totalEmissions,
        scope1: scope1InTons,
        scope2: scope2InTons,
        scope2Market: scope2MarketInTons,
        scope3: scope3InTons,
        scope1Percentage,
        scope2Percentage,
        scope3Percentage,
        dataQualityScore: dataQualityScore?.overallScore || 0,
        evidenceCount: evidenceFiles?.length || 0
      },
      topEmissionSources,
      scope3Analysis,
      activities: activities.map(a => ({
        ...a,
        emissions: (safeParseNumber(a.amount) * safeParseNumber(a.factor)) / 1000
      })),
      evidenceFiles: evidenceFiles || [],
      uncertaintyAnalysis: results.uncertainty_analysis || null,
      dataQuality: dataQualityScore || null,
      chartElements: [], // Add if you have charts to include
      companyProfile: {
        sector: 'Services', // Update based on your data
        employees: 0,
        revenue: 0,
        operations: []
      }
    };
    
    return pdfData;
  };'''
    
    # Find the start of the preparePDFExportData function
    # Look for the function definition
    pattern = r'(  // FIXED: Prepare comprehensive PDF export data\n)?  const preparePDFExportData = \(\) => \{'
    match = re.search(pattern, content)
    
    if not match:
        # Try alternative pattern without the comment
        pattern = r'  const preparePDFExportData = \(\) => \{'
        match = re.search(pattern, content)
    
    if not match:
        print("❌ Could not find preparePDFExportData function")
        return False
    
    start_pos = match.start()
    
    # Find the end of the function by counting braces
    brace_count = 0
    in_string = False
    escape_next = False
    pos = match.end() - 1  # Start from the opening brace
    
    while pos < len(content):
        char = content[pos]
        
        # Handle string literals
        if not escape_next:
            if char in ['"', "'", '`'] and not in_string:
                in_string = char
            elif char == in_string:
                in_string = False
            elif char == '\\':
                escape_next = True
        else:
            escape_next = False
        
        # Count braces only outside strings
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = pos + 2  # Include the closing brace and semicolon
                    break
        
        pos += 1
    
    if brace_count != 0:
        print("❌ Could not find matching closing brace for preparePDFExportData")
        return False
    
    # Replace the function
    new_content = content[:start_pos] + new_function + content[end_pos:]
    
    # Write the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Successfully updated preparePDFExportData function")
    return True

def main():
    """Main function"""
    # Get current directory
    current_dir = os.getcwd()
    expected_dir = "/Users/isaiah/Documents/Scope3Tool"
    
    # Check if we're in the right directory
    if current_dir != expected_dir:
        print(f"⚠️  Current directory: {current_dir}")
        print(f"📂 Expected directory: {expected_dir}")
        print("\nNavigating to correct directory...")
        try:
            os.chdir(expected_dir)
            print(f"✅ Changed to: {os.getcwd()}")
        except Exception as e:
            print(f"❌ Could not change directory: {e}")
            print(f"\nPlease run this command first:")
            print(f"cd {expected_dir}")
            return
    
    # Common possible paths for the file
    possible_paths = [
        "src/components/emissions/EliteGHGCalculator.tsx",
        "src/components/EliteGHGCalculator.tsx",
        "components/emissions/EliteGHGCalculator.tsx",
        "components/EliteGHGCalculator.tsx",
        "app/components/emissions/EliteGHGCalculator.tsx",
        "app/components/EliteGHGCalculator.tsx"
    ]
    
    # Find the file
    file_path = None
    for path in possible_paths:
        full_path = os.path.join(expected_dir, path)
        if os.path.exists(full_path):
            file_path = full_path
            break
    
    if not file_path:
        print("❌ Could not find EliteGHGCalculator.tsx")
        print("\nSearching for .tsx files...")
        # Search for any .tsx files
        for root, dirs, files in os.walk(expected_dir):
            for file in files:
                if file == "EliteGHGCalculator.tsx":
                    file_path = os.path.join(root, file)
                    print(f"✅ Found file at: {file_path}")
                    break
            if file_path:
                break
    
    if not file_path:
        print("\n❌ EliteGHGCalculator.tsx not found in project")
        print("Please check if the file exists in your project")
        return
    
    print(f"\n📁 Processing: {file_path}")
    
    # Create backup
    backup_path = create_backup(file_path)
    
    # Update the function
    success = update_prepare_pdf_export_data(file_path)
    
    if success:
        print("\n✨ Update complete!")
        print(f"Original file backed up to: {backup_path}")
        print("\nThe preparePDFExportData function has been updated with:")
        print("- Multiple field name checks for API response")
        print("- Intelligent unit detection (kg vs tons)")
        print("- Activity-based calculation fallback")
        print("- Scope 2 fix for zero values")
        print("- Debug logging")
        print("\n🚀 Your PDF exports should now show correct Scope 2 values!")
    else:
        print("\n❌ Update failed!")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()