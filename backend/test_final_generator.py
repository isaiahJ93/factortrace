#!/usr/bin/env python3
"""Test the fully fixed ESRS generator"""

import sys
sys.path.insert(0, '/Users/isaiah/Documents/Scope3Tool/backend')

from app.api.v1.endpoints.esrs_e1_full_final import generate_xbrl_report

# Comprehensive test data
test_data = {
    'organization': 'Test Corp',
    'entity_name': 'Test Corp',
    'lei': 'TEST123456789012345',
    'reporting_period': 2025,
    'language': 'en',
    'governance': {
        'board_oversight': True,
        'management_responsibility': True,
        'board_meetings_climate': 4,
        'climate_expertise': True,
        'climate_committee': True,
        'climate_incentives': True
    },
    'materiality': {
        'impact_material': True,
        'financial_material': True
    },
    'emissions': {
        'scope1': 100,
        'scope2_location': 200,
        'scope2_market': 180,
        'scope3': 300
    },
    'energy': {
        'fossil': 1000,
        'renewable': 500,
        'total': 1500
    },
    'policies': [
        {'name': 'Climate Policy', 'description': 'Our climate policy'}
    ],
    'actions': [
        {'description': 'Solar installation', 'investment_meur': 5}
    ],
    'targets': [
        {'target_year': 2030, 'reduction_percent': 50}
    ]
}

print("Generating final XBRL report...")
try:
    report = generate_xbrl_report(test_data)
    
    output_file = 'esrs_e1_final_output.xhtml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Generated {output_file}")
    print(f"File size: {len(report):,} bytes")
    
    # Detailed analysis
    print("\n=== STRUCTURE ANALYSIS ===")
    print(f"<html> tags: {report.count('<html')}")
    print(f"<head> tags: {report.count('<head>')}")
    print(f"</head> tags: {report.count('</head>')}")
    print(f"<body> tags: {report.count('<body>')}")
    print(f"Empty names: {report.count('name=""')}")
    
    print("\n=== XBRL FACTS ===")
    print(f"Total XBRL facts: {report.count('<ix:non')}")
    print(f"Emission facts: {report.count('esrs:Gross')}")
    print(f"Energy facts: {report.count('esrs:Energy')}")
    
    # Final check
    if report.count('name=""') == 0 and report.count('<head>') == 1:
        print("\n🎉 SUCCESS: All structural issues fixed!")
    else:
        print("\n⚠️  Some issues remain - check validation")
        
    print(f"\nValidate with:")
    print(f"poetry run arelleCmdLine --file {output_file} --validate")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
