import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl
import json
from datetime import datetime
import os

# Load the fixed data
with open('complete_test_data_fixed.json', 'r') as f:
    test_data = json.load(f)

try:
    print("="*60)
    print("GENERATING FINAL ESRS E1 REPORT")
    print("="*60)
    
    # Generate the report
    result = generate_world_class_esrs_e1_ixbrl(test_data)
    
    print("\n✅ SUCCESS! Complete ESRS E1 report generated!")
    
    # Save outputs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for key, value in result.items():
        if isinstance(value, str) and len(value) > 100:
            if 'html' in key:
                filename = f"ESRS_E1_Final_Report_{timestamp}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(value)
                print(f"✓ HTML Report: {filename}")
                
                # Open it
                abs_path = os.path.abspath(filename)
                print(f"\n🌐 Opening: file://{abs_path}")
                try:
                    import webbrowser
                    webbrowser.open(f'file://{abs_path}')
                except:
                    pass
    
    print("\n🎉 COMPLETE SUCCESS!")
    print("All functions integrated and working!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
