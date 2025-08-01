#!/usr/bin/env python3
"""Apply fix for ghg_breakdown list vs dict issue"""

import re

# Read the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find the extract_ghg_breakdown function
pattern = r'def extract_ghg_breakdown\(data\):(.*?)(?=\ndef|\nclass|\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    print("Found extract_ghg_breakdown function")
    
    # Replace with the fixed version
    fixed_function = '''def extract_ghg_breakdown(data):
    """Extract GHG breakdown from data"""
    ghg_breakdown_list = data.get('ghg_breakdown', [])
    
    # Handle the list of emission activities
    if isinstance(ghg_breakdown_list, list):
        # Sum up all emissions from the list
        total_co2e = sum(
            item.get('emissions_kg_co2e', 0) / 1000  # Convert kg to tonnes
            for item in ghg_breakdown_list
        )
        
        # Group by scope for detailed breakdown
        scope_breakdown = {
            'scope1': 0,
            'scope2': 0,
            'scope3': 0,
            'total': 0
        }
        
        for item in ghg_breakdown_list:
            scope = item.get('scope', '').lower()
            emissions_tonnes = item.get('emissions_kg_co2e', 0) / 1000
            
            if scope == '1':
                scope_breakdown['scope1'] += emissions_tonnes
            elif scope == '2':
                scope_breakdown['scope2'] += emissions_tonnes
            elif scope == '3':
                scope_breakdown['scope3'] += emissions_tonnes
            
            scope_breakdown['total'] += emissions_tonnes
        
        # Return in expected format
        return {
            'CO2_tonnes': scope_breakdown['total'],
            'CH4_tonnes_co2e': 0,
            'N2O_tonnes_co2e': 0,
            'other_ghg_tonnes_co2e': 0,
            'total_tonnes_co2e': scope_breakdown['total'],
            'scope_breakdown': scope_breakdown,
            'detailed_activities': ghg_breakdown_list
        }
    
    # Fallback for old format (if data is already a dict)
    elif isinstance(ghg_breakdown_list, dict):
        ghg_data = ghg_breakdown_list
        return {
            'CO2_tonnes': ghg_data.get('CO2_tonnes', 0),
            'CH4_tonnes_co2e': ghg_data.get('CH4_tonnes_co2e', 0),
            'N2O_tonnes_co2e': ghg_data.get('N2O_tonnes_co2e', 0),
            'other_ghg_tonnes_co2e': ghg_data.get('other_ghg_tonnes_co2e', 0),
            'total_tonnes_co2e': (
                ghg_data.get('CO2_tonnes', 0) +
                ghg_data.get('CH4_tonnes_co2e', 0) +
                ghg_data.get('N2O_tonnes_co2e', 0) +
                ghg_data.get('other_ghg_tonnes_co2e', 0)
            )
        }
    
    # Default empty response
    return {
        'CO2_tonnes': 0,
        'CH4_tonnes_co2e': 0,
        'N2O_tonnes_co2e': 0,
        'other_ghg_tonnes_co2e': 0,
        'total_tonnes_co2e': 0
    }'''
    
    # Replace in content
    content = content[:match.start()] + fixed_function + content[match.end():]
    
    # Write back
    with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed extract_ghg_breakdown function")
    
    # Test compilation
    import subprocess
    result = subprocess.run(['python', '-m', 'py_compile', 'app/api/v1/endpoints/esrs_e1_full.py'], 
                           capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ File compiles successfully!")
    else:
        print("❌ Compilation error:", result.stderr)
else:
    print("❌ Could not find extract_ghg_breakdown function")