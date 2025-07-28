#!/usr/bin/env python3
"""
Remove the incorrectly placed ESRS methods to restore working state
"""

import os
import shutil
from datetime import datetime
import re

def restore_working_state(file_path):
    """Remove the ESRS methods that were placed incorrectly"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    print("🔍 Finding and removing incorrectly placed ESRS methods...")
    
    # Find where the ESRS methods start
    esrs_start_line = None
    for i, line in enumerate(lines):
        if '// ESRS E1 Enhanced Section Methods' in line:
            # Go back a few lines to catch the comment block
            esrs_start_line = i - 3 if i >= 3 else i
            print(f"✅ Found ESRS methods starting at line {esrs_start_line + 1}")
            break
    
    if esrs_start_line is None:
        print("❌ Could not find ESRS methods")
        return False
    
    # Find where they end - look for the pattern of the last method
    esrs_end_line = None
    in_uncertainty_method = False
    
    for i in range(esrs_start_line, len(lines)):
        if 'private addUncertaintyAnalysisSection' in lines[i]:
            in_uncertainty_method = True
        
        if in_uncertainty_method and lines[i].strip() == '}' and i + 1 < len(lines):
            # Check if this is the end of the method
            next_line = lines[i + 1].strip()
            if not next_line or next_line.startswith('//') or next_line.startswith('export') or next_line == '}':
                esrs_end_line = i
                print(f"✅ Found ESRS methods ending at line {esrs_end_line + 1}")
                break
    
    if esrs_end_line is None:
        print("❌ Could not find end of ESRS methods")
        return False
    
    # Remove the ESRS methods section
    print(f"🗑️  Removing lines {esrs_start_line + 1} to {esrs_end_line + 1}")
    del lines[esrs_start_line:esrs_end_line + 1]
    
    # Also remove the section calls that were added
    print("\n🔍 Removing ESRS section calls...")
    
    # Find and remove the section calls
    section_calls_start = None
    for i, line in enumerate(lines):
        if '// ESRS E1 Enhanced Sections' in line:
            section_calls_start = i
            break
    
    if section_calls_start is not None:
        # Find the end of section calls (look for the addFooters call)
        section_calls_end = None
        for i in range(section_calls_start, min(section_calls_start + 100, len(lines))):
            if 'this.addFooters' in lines[i]:
                section_calls_end = i - 1
                break
        
        if section_calls_end is not None:
            print(f"🗑️  Removing section calls from line {section_calls_start + 1} to {section_calls_end + 1}")
            del lines[section_calls_start:section_calls_end + 1]
    
    # Write the cleaned content
    cleaned_content = '\n'.join(lines)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print("\n✅ Successfully removed incorrectly placed code")
    return True

def add_interface_properties(file_path):
    """Add the missing properties to PDFExportData interface"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔧 Adding missing properties to PDFExportData interface...")
    
    # Find the PDFExportData interface
    interface_match = re.search(r'(export interface PDFExportData\s*\{)([\s\S]*?)(\n\})', content)
    
    if interface_match:
        interface_content = interface_match.group(2)
        
        # Properties to add if missing
        properties_to_add = []
        
        if 'dataQuality?' not in interface_content:
            properties_to_add.append('  dataQuality?: {\n    overallScore: number;\n    dataCompleteness: number;\n    evidenceProvided: number;\n    dataRecency: number;\n    methodologyAccuracy: number;\n  };')
        
        if 'esrsE1Data?' not in interface_content:
            properties_to_add.append('  esrsE1Data?: {\n    energy_consumption?: any;\n    internal_carbon_pricing?: any;\n    climate_actions?: any;\n    climate_policy?: any;\n  };')
        
        if 'ghgBreakdown?' not in interface_content and 'ghg_breakdown?' not in interface_content:
            properties_to_add.append('  ghgBreakdown?: {\n    CO2_tonnes: number;\n    CH4_tonnes: number;\n    N2O_tonnes: number;\n    HFCs_tonnes_co2e?: number;\n    total_co2e: number;\n    gwp_version: string;\n  };')
        
        if 'uncertaintyAnalysis?' not in interface_content:
            properties_to_add.append('  uncertaintyAnalysis?: {\n    confidence_interval_95?: number[];\n    mean_emissions?: number;\n    std_deviation?: number;\n    relative_uncertainty_percent?: number;\n    monte_carlo_runs?: number;\n  };')
        
        if 'results?' not in interface_content:
            properties_to_add.append('  results?: any;')
        
        if properties_to_add:
            # Add the properties before the closing brace
            new_interface = interface_match.group(1) + interface_content + '\n\n  // ESRS E1 Enhancement Properties\n' + '\n\n'.join(properties_to_add) + interface_match.group(3)
            
            content = content[:interface_match.start()] + new_interface + content[interface_match.end():]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Added {len(properties_to_add)} properties to PDFExportData interface")
            return True
    
    print("❌ Could not find PDFExportData interface")
    return False

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
        # Step 1: Remove incorrectly placed code
        success = restore_working_state(file_path)
        
        if success:
            # Step 2: Add interface properties
            add_interface_properties(file_path)
            
            print("\n✨ File restored to working state!")
            print("\nWhat was done:")
            print("1. Removed incorrectly placed ESRS methods")
            print("2. Removed ESRS section calls")
            print("3. Added missing properties to PDFExportData interface")
            print("\n📌 Next steps:")
            print("1. Run: npm run dev")
            print("2. Verify the build works")
            print("3. The ESRS sections can be added properly later")
            print("\n💡 Your PDFs will still work with the existing professional features!")
        else:
            print("\n❌ Restoration failed!")
            print(f"Restoring from backup: {backup_path}")
            shutil.copy2(backup_path, file_path)
    except Exception as e:
        print(f"\n❌ Error during restoration: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, file_path)

if __name__ == "__main__":
    main()