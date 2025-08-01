#!/usr/bin/env python3
"""Fix the extract_ghg_breakdown function"""

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# The fixed function
fixed_function = '''def extract_ghg_breakdown(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract GHG breakdown by gas type"""
    ghg_breakdown_raw = data.get('ghg_breakdown', [])
    
    # Handle list format (current data structure)
    if isinstance(ghg_breakdown_raw, list):
        # Initialize gas totals
        gas_totals = {
            'CO2_tonnes': 0,
            'CH4_tonnes': 0,
            'N2O_tonnes': 0,
            'HFCs_tonnes_co2e': 0,
            'PFCs_tonnes_co2e': 0,
            'SF6_tonnes': 0,
            'NF3_tonnes': 0
        }
        
        # Sum emissions from all activities
        for item in ghg_breakdown_raw:
            # Convert kg to tonnes
            emissions_tonnes = item.get('emissions_kg_co2e', 0) / 1000
            # For now, classify all as CO2 (you can enhance this based on activity_type)
            gas_totals['CO2_tonnes'] += emissions_tonnes
        
        # Calculate total CO2e with GWP factors
        total_co2e = (
            gas_totals['CO2_tonnes'] +
            gas_totals['CH4_tonnes'] * 25 +
            gas_totals['N2O_tonnes'] * 298 +
            gas_totals['HFCs_tonnes_co2e'] +
            gas_totals['PFCs_tonnes_co2e'] +
            gas_totals['SF6_tonnes'] * 22800 +
            gas_totals['NF3_tonnes'] * 17200
        )
        
        return {
            'total_co2e': total_co2e,
            **gas_totals
        }
    
    # Handle dict format (backward compatibility)
    elif isinstance(ghg_breakdown_raw, dict):
        ghg_data = ghg_breakdown_raw
        # Calculate total CO2e
        total_co2e = (
            ghg_data.get('CO2_tonnes', 0) +
            ghg_data.get('CH4_tonnes', 0) * 25 +
            ghg_data.get('N2O_tonnes', 0) * 298 +
            ghg_data.get('HFCs_tonnes_co2e', 0) +
            ghg_data.get('PFCs_tonnes_co2e', 0) +
            ghg_data.get('SF6_tonnes', 0) * 22800 +
            ghg_data.get('NF3_tonnes', 0) * 17200
        )
        return {
            'total_co2e': total_co2e,
            **ghg_data
        }
    
    # Default empty response
    return {
        'total_co2e': 0,
        'CO2_tonnes': 0,
        'CH4_tonnes': 0,
        'N2O_tonnes': 0,
        'HFCs_tonnes_co2e': 0,
        'PFCs_tonnes_co2e': 0,
        'SF6_tonnes': 0,
        'NF3_tonnes': 0
    }
'''

# Replace lines 7459-7475 (the old function)
new_lines = lines[:7458] + [fixed_function + '\n'] + lines[7475:]

# Write back
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Fixed extract_ghg_breakdown function")

# Test compilation
import subprocess
result = subprocess.run(['python', '-m', 'py_compile', 'app/api/v1/endpoints/esrs_e1_full.py'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✅ File compiles successfully!")
    print("\n🚀 Your ESRS report generator should now work with the list-based ghg_breakdown data!")
else:
    print("❌ Compilation error:", result.stderr)