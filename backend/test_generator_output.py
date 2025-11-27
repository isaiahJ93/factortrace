#!/usr/bin/env python3
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl

try:
    result = generate_world_class_esrs_e1_ixbrl({
        'entity_name': 'Test Corp',
        'reporting_period': 2025,
        'lei': 'TEST123456789012345',
        'gross_scope1_emissions': 100,
        'gross_scope2_location_based': 50,
        'gross_scope3_emissions': 200,
    })
    
    # Use 'content' key instead of 'xbrl_content'
    if 'content' in result:
        content = result['content']
        
        # Save output
        with open('test_output.xhtml', 'w') as f:
            f.write(content)
        
        print("=== GENERATOR OUTPUT CHECK ===")
        print(f"✅ Correct namespace: {'https://xbrl.efrag.org/taxonomy/esrs/2023-12-22' in content}")
        print(f"✅ Correct schema: {'common/esrs_cor.xsd' in content}")
        print(f"✅ No wrong units: {'esrs:metricTonnesCO2e' not in content}")
        print(f"✅ Has duration periods: {'xbrli:startDate' in content}")
        
        # Check for remaining issues
        issues = []
        if 'xbrli:instant' in content:
            issues.append("Still using instant periods")
        if 'esrs:metricTonnesCO2e' in content:
            issues.append("Still using old unit names")
        if 'esrs_all.xsd' in content:
            issues.append("Still using wrong schema")
            
        if issues:
            print(f"\n⚠️ Issues found: {', '.join(issues)}")
        else:
            print("\n🎉 All checks passed!")
        
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()
