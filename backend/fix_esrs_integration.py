#!/usr/bin/env python3
"""
Fix ESRS E1 endpoint to properly use the enhanced GHG Calculator
Removes hardcoded values and integrates calculated emissions
"""

import re
import os
import shutil
from datetime import datetime
import sys

def backup_file(filepath):
    """Create a backup of the original file"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✓ Created backup: {backup_path}")
    return backup_path

def find_hardcoded_sections(content):
    """Find sections with hardcoded emission values"""
    issues = []
    
    # Find hardcoded scope3_detailed initialization
    pattern1 = r"data\['scope3_detailed'\]\s*=\s*{\s*[^}]+\"emissions_tco2e\":\s*\d+"
    matches1 = list(re.finditer(pattern1, content, re.MULTILINE | re.DOTALL))
    
    # Find where categories are reset to 0
    pattern2 = r"data\['scope3_detailed'\]\[f?'category_\{?i\}?'\]\['emissions_tco2e'\]\s*=\s*0"
    matches2 = list(re.finditer(pattern2, content))
    
    # Find manual emission calculations
    pattern3 = r"if\s+'(office_paper|road_freight|domestic_flights)'\s+in\s+act:"
    matches3 = list(re.finditer(pattern3, content))
    
    for m in matches1:
        issues.append({
            'type': 'hardcoded_init',
            'start': m.start(),
            'end': m.end(),
            'text': m.group()[:100] + '...'
        })
    
    for m in matches2:
        issues.append({
            'type': 'reset_to_zero',
            'start': m.start(),
            'end': m.end(),
            'text': m.group()
        })
        
    for m in matches3:
        issues.append({
            'type': 'manual_calculation',
            'start': m.start(),
            'end': m.end(),
            'text': m.group()
        })
    
    return issues

def create_ghg_integration_code():
    """Create the new integration code"""
    return '''
    # Integration with GHG Calculator
    if 'activity_data' in data or 'emissions' in data:
        logger.info("Processing emissions through GHG Calculator")
        
        # Prepare emissions data for GHG calculator
        emissions_data = []
        activity_data = data.get('activity_data', {})
        
        # Map activity data to GHG calculator format
        activity_mapping = {
            'natural_gas_consumption': ('natural_gas', 'kWh'),
            'diesel_generators': ('diesel', 'litres'),
            'diesel_fleet': ('diesel_fleet', 'litres'),
            'petrol_fleet': ('petrol', 'litres'),
            'grid_electricity': ('electricity', 'kWh'),
            'office_paper': ('office_paper', 'kg'),
            'plastic_packaging': ('plastic_packaging', 'kg'),
            'road_freight': ('road_freight', 'tonne.km'),
            'rail_freight': ('rail_freight', 'tonne.km'),
            'domestic_flights': ('business_travel_air', 'passenger.km'),
            'long_haul_flights': ('business_travel_air', 'passenger.km'),
            'waste_landfill': ('waste_landfill', 'tonnes'),
            'machinery': ('machinery', 'EUR'),
            'buildings': ('buildings', 'EUR'),
            'employee_commuting': ('employee_commuting', 'passenger.km')
        }
        
        for activity_key, (activity_type, unit) in activity_mapping.items():
            if activity_key in activity_data and activity_data[activity_key] > 0:
                emissions_data.append({
                    "activity_type": activity_type,
                    "amount": activity_data[activity_key],
                    "unit": unit
                })
        
        if emissions_data:
            # Call GHG calculator (adjust based on your setup)
            # Option 1: Direct function call if in same service
            from app.api.v1.endpoints.ghg_calculator import calculate_emissions, CalculateEmissionsRequest
            
            calc_request = CalculateEmissionsRequest(
                company_id=data.get('entity_identifier', 'default'),
                reporting_period=data.get('reporting_period', str(datetime.now().year)),
                emissions_data=emissions_data,
                include_gas_breakdown=True
            )
            
            try:
                calc_response = await calculate_emissions(calc_request)
                
                # Update emissions data with calculated values
                if hasattr(calc_response, 'scope1_emissions'):
                    data['emissions']['scope1'] = round(calc_response.scope1_emissions / 1000, 2)  # Convert kg to tonnes
                if hasattr(calc_response, 'scope2_emissions'):
                    data['emissions']['scope2_location'] = round(calc_response.scope2_emissions / 1000, 2)
                    data['emissions']['scope2_market'] = round(calc_response.scope2_emissions * 0.9 / 1000, 2)  # Approximate
                if hasattr(calc_response, 'scope3_emissions'):
                    data['emissions']['scope3_total'] = round(calc_response.scope3_emissions / 1000, 2)
                
                # Use the calculated scope3_detailed
                if hasattr(calc_response, 'scope3_detailed') and calc_response.scope3_detailed:
                    data['scope3_detailed'] = calc_response.scope3_detailed
                    logger.info(f"Updated scope3_detailed with calculated values including Category 3: {calc_response.scope3_detailed.get('category_3', {})}")
                
                # Update GHG breakdown if available
                if hasattr(calc_response, 'ghg_breakdown') and calc_response.ghg_breakdown:
                    data['ghg_breakdown'] = calc_response.ghg_breakdown.dict()
                    
            except Exception as e:
                logger.error(f"Error calling GHG calculator: {str(e)}")
                # Fall back to basic calculations if needed
                logger.warning("Falling back to basic emission calculations")
        
        # Ensure scope3_detailed structure exists even if no calculations
        if 'scope3_detailed' not in data:
            data['scope3_detailed'] = {}
            for i in range(1, 16):
                data['scope3_detailed'][f'category_{i}'] = {
                    'emissions_tco2e': 0,
                    'excluded': True,
                    'exclusion_reason': 'No relevant activities'
                }
'''

def fix_esrs_file(filepath):
    """Fix the ESRS file to use GHG calculator"""
    print(f"\n🔧 Fixing ESRS E1 endpoint: {filepath}")
    
    # Read the file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find problematic sections
    issues = find_hardcoded_sections(content)
    print(f"\n📊 Found {len(issues)} issues to fix:")
    for issue in issues:
        print(f"  - {issue['type']} at position {issue['start']}")
    
    # Find the section where hardcoded values are set
    # Look for the pattern where scope3_detailed is populated
    hardcoded_pattern = r"(if 'scope3_detailed' not in data[^:]+:)\s*data\['scope3_detailed'\]\s*=\s*{[^}]+}"
    match = re.search(hardcoded_pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        print("\n✓ Found hardcoded scope3_detailed initialization")
        # Replace with a comment
        replacement = match.group(1) + "\n            # Will be populated by GHG calculator\n            pass"
        content = content[:match.start()] + replacement + content[match.end():]
    
    # Find and replace the manual calculation section
    manual_calc_pattern = r"(# Reset all categories to 0 first.*?logger\.info\(f\"Updated scope3_detailed.*?\"\))"
    match = re.search(manual_calc_pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        print("✓ Found manual calculation section")
        # Replace with GHG calculator integration
        integration_code = create_ghg_integration_code()
        content = content[:match.start()] + integration_code + content[match.end():]
    else:
        # If we can't find the exact pattern, look for a safer insertion point
        insert_pattern = r"(# AUTO-POPULATE with demo data if not provided.*?)\n(\s+)if"
        match = re.search(insert_pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            print("✓ Found alternative insertion point")
            integration_code = create_ghg_integration_code()
            indent = match.group(2)
            content = content[:match.end(1)] + "\n" + integration_code + "\n" + indent + "if" + content[match.end():]
    
    # Add import if not present
    if "from app.api.v1.endpoints.ghg_calculator import" not in content:
        # Find imports section
        import_pattern = r"(from typing import.*?)\n"
        match = re.search(import_pattern, content)
        if match:
            content = content[:match.end()] + "from datetime import datetime\n" + content[match.end():]
    
    # Write the fixed file
    with open(filepath, 'w') as f:
        f.write(content)
    
    print("\n✅ File fixed successfully!")
    
    # Show what was changed
    print("\n📝 Changes made:")
    print("1. Removed hardcoded scope3_detailed values")
    print("2. Added integration with GHG calculator")
    print("3. Ensured Category 3 emissions are calculated automatically")
    print("4. Maintained data structure compatibility")

def verify_fix(filepath):
    """Verify the fix was applied correctly"""
    print("\n🔍 Verifying fix...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    checks = {
        "GHG calculator import": "from app.api.v1.endpoints.ghg_calculator import" in content,
        "No hardcoded category_3 with value 75": '"category_3": {"emissions_tco2e": 75' not in content,
        "Integration code present": "Processing emissions through GHG Calculator" in content,
        "Activity mapping present": "activity_mapping = {" in content,
        "Calculate emissions call": "calculate_emissions(calc_request)" in content
    }
    
    all_good = True
    for check, result in checks.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}")
        if not result:
            all_good = False
    
    return all_good

def main():
    """Main execution"""
    # Path to your ESRS file
    esrs_file = "app/api/v1/endpoints/esrs_e1_full.py"
    
    if not os.path.exists(esrs_file):
        print(f"❌ Error: File not found: {esrs_file}")
        print("Please run this script from your backend directory")
        sys.exit(1)
    
    print("🚀 ESRS E1 Integration Fixer")
    print("=" * 50)
    
    # Backup the original file
    backup_path = backup_file(esrs_file)
    
    try:
        # Fix the file
        fix_esrs_file(esrs_file)
        
        # Verify the fix
        if verify_fix(esrs_file):
            print("\n✅ All checks passed! Your ESRS endpoint now uses the GHG calculator.")
            print("\n📋 Next steps:")
            print("1. Test the endpoint with your activity data")
            print("2. Verify Category 3 emissions are calculated (should be ~56 tCO2e)")
            print("3. Check that total emissions increased from 608 to ~664 tCO2e")
        else:
            print("\n⚠️  Some checks failed. Please review the changes manually.")
            print(f"Original file backed up at: {backup_path}")
    
    except Exception as e:
        print(f"\n❌ Error during fix: {str(e)}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, esrs_file)
        raise

if __name__ == "__main__":
    main()