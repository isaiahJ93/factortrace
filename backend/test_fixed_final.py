#!/usr/bin/env python3
"""Test the fixed ESRS generator"""

import sys
sys.path.insert(0, '/Users/isaiah/Documents/Scope3Tool/backend')

# Import from fixed file
from app.api.v1.endpoints.esrs_e1_full_fixed import generate_xbrl_report

# Test data
test_data = {
    'organization': 'Test Corp',
    'entity_name': 'Test Corp',
    'lei': 'TEST123456789012345',
    'reporting_period': 2025,
    'governance': {
        'board_oversight': True,
        'management_responsibility': True,
        'board_meetings_climate': 4,
        'climate_expertise': True
    },
    'materiality': {
        'impact_material': True,
        'financial_material': True
    },
    'emissions': {
        'scope1': 100,
        'scope2_location': 200,
        'scope3': 300
    },
    'energy': {
        'fossil': 1000,
        'renewable': 500
    }
}

print("Generating XBRL report...")
try:
    report = generate_xbrl_report(test_data)
    
    # Save output
    output_file = 'test_fixed_final.xhtml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Analyze output
    print(f"\n✅ Generated {output_file}")
    print(f"File size: {len(report)} bytes")
    print(f"<head> tags: {report.count('<head>')}")
    print(f"<html> tags: {report.count('<html')}")  
    print(f"Empty names: {report.count('name=\"\"')}")
    print(f"Proper emission facts: {report.count('esrs:Gross')}")
    
    # Check for issues
    issues = []
    if report.count('<head>') > 1:
        issues.append("Multiple <head> tags")
    if report.count('name=""') > 0:
        issues.append("Empty name attributes")
    if report.count('<html') > 1:
        issues.append("Multiple <html> tags")
        
    if issues:
        print(f"\n❌ Issues found: {', '.join(issues)}")
    else:
        print("\n✅ No structural issues found!")
        
    print(f"\nValidate with: poetry run arelleCmdLine --file {output_file} --validate")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
