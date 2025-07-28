#!/usr/bin/env python3
"""
Fix property references in PDF methods
"""

import os
import shutil
from datetime import datetime
import re

def fix_property_references(file_path):
    """Fix undefined property references in PDF methods"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Fixing property references...")
    
    # Fix the addActivityDetails method
    # The activity object might have different property names
    old_activity_code = r'''act\.emissionFactor\.toFixed\(3\)'''
    new_activity_code = '''(act.emissionFactor || act.factor || 0).toFixed(3)'''
    
    content = re.sub(old_activity_code, new_activity_code, content)
    
    # Fix other potential property issues
    # Replace direct property access with safe access
    replacements = [
        # Activity properties
        (r'act\.name\.substring', '(act.name || act.activity || "").substring'),
        (r'act\.category', '(act.category || act.scope || "")'),
        (r'act\.quantity', '(act.quantity || act.amount || 0)'),
        (r'act\.unit', '(act.unit || "")'),
        (r'act\.emissions\.toFixed', '(act.emissions || act.totalEmissions || 0).toFixed'),
        
        # Summary properties
        (r'data\.summary\.scope1Percentage\.toFixed', '(data.summary.scope1Percentage || 0).toFixed'),
        (r'data\.summary\.scope2Percentage\.toFixed', '(data.summary.scope2Percentage || 0).toFixed'),
        (r'data\.summary\.scope3Percentage\.toFixed', '(data.summary.scope3Percentage || 0).toFixed'),
        
        # Category properties
        (r'cat\.emissions\.toFixed', '(cat.emissions || 0).toFixed'),
        (r'cat\.percentage', '(cat.percentage || 0)'),
        (r'cat\.count', '(cat.count || 0)'),
        (r'cat\.status', '(cat.status || "N/A")'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Update the activity details table creation to handle missing data better
    activity_section = re.search(r'(const activityData = activities[\s\S]*?\];)', content)
    
    if activity_section:
        new_activity_code = '''const activityData = activities.slice(0, 20).map(act => [
        (act.name || act.activity || "").substring(0, 30),
        (act.category || act.scope || ""),
        (act.quantity || act.amount || 0) + ' ' + (act.unit || ""),
        (act.emissionFactor || act.factor || 0).toFixed(3),
        (act.emissions || act.totalEmissions || 0).toFixed(3) + ' tCO2e'
      ]);'''
        
        content = content.replace(activity_section.group(1), new_activity_code)
    
    # Also fix scope3Categories mapping
    category_section = re.search(r'(const categoryData = categories[\s\S]*?\];)', content)
    
    if category_section:
        new_category_code = '''const categoryData = categories.map(cat => [
        cat.category || cat.name || "",
        (cat.emissions || 0).toFixed(3) + ' tCO2e',
        (cat.percentage || 0).toFixed(1) + '%',
        cat.count || cat.activities || 0,
        cat.status || "Calculated"
      ]);'''
        
        content = content.replace(category_section.group(1), new_category_code)
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed property references")
    return True

def add_data_validation(file_path):
    """Add data validation to prevent runtime errors"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Adding data validation...")
    
    # Update the reconcileData method to ensure all properties exist
    reconcile_match = re.search(r'(private reconcileData\(data: PDFExportData\): PDFExportData \{[\s\S]*?\})', content)
    
    if reconcile_match:
        new_reconcile = '''private reconcileData(data: PDFExportData): PDFExportData {
    // Ensure all required properties exist
    const reconciled = {
      ...data,
      metadata: {
        documentId: data.metadata?.documentId || 'GHG-' + Date.now().toString(36).toUpperCase(),
        companyName: data.metadata?.companyName || 'Your Company',
        reportingPeriod: data.metadata?.reportingPeriod || new Date().toISOString().slice(0, 7),
        generatedDate: data.metadata?.generatedDate || new Date().toISOString(),
        standard: data.metadata?.standard || 'ESRS E1 Compliant',
        methodology: data.metadata?.methodology || 'GHG Protocol Corporate Standard',
        ...data.metadata
      },
      summary: {
        totalEmissions: data.summary?.totalEmissions || 0,
        scope1: data.summary?.scope1 || 0,
        scope2: data.summary?.scope2 || 0,
        scope3: data.summary?.scope3 || 0,
        scope1Percentage: 0,
        scope2Percentage: 0,
        scope3Percentage: 0,
        dataQualityScore: data.summary?.dataQualityScore || 72,
        ...data.summary
      }
    };
    
    // Calculate percentages
    const total = reconciled.summary.totalEmissions;
    if (total > 0) {
      reconciled.summary.scope1Percentage = (reconciled.summary.scope1 / total * 100);
      reconciled.summary.scope2Percentage = (reconciled.summary.scope2 / total * 100);
      reconciled.summary.scope3Percentage = (reconciled.summary.scope3 / total * 100);
    }
    
    // Ensure arrays exist
    reconciled.activities = data.activities || [];
    reconciled.scope3Categories = data.scope3Categories || [];
    reconciled.targets = data.targets || [];
    reconciled.topEmissionSources = data.topEmissionSources || [];
    
    return reconciled;
  }'''
        
        content = content.replace(reconcile_match.group(1), new_reconcile)
        print("✅ Updated reconcileData method with validation")
    
    # Write the updated content
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
        # Fix property references
        success1 = fix_property_references(file_path)
        
        # Add data validation
        success2 = add_data_validation(file_path)
        
        if success1 and success2:
            print("\n✨ Successfully fixed property access issues!")
            print("\nFixed:")
            print("✓ Safe property access with fallbacks")
            print("✓ Handle different property names (emissionFactor/factor)")
            print("✓ Added null/undefined checks")
            print("✓ Enhanced data validation in reconcileData")
            print("\n🚀 The PDF export should now handle missing properties gracefully!")
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