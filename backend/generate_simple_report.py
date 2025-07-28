import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import generate_world_class_esrs_e1_ixbrl
import json
from datetime import datetime

# Minimal test data
test_data = {
    "force_generation": True,
    "organization": "Test Corp",
    "lei": "5493000KJTIIGC8Y1R12",
    "reporting_period": 2024,
    "emissions": {
        "scope1": 15000,
        "scope2": 6500,
        "scope3": 120000
    },
    "scope3_detailed": {
        f"category_{i}": {"emissions_tco2e": 8000, "excluded": False}
        for i in range(1, 16)
    },
    "targets": {
        "base_year": 2020,
        "targets": [{"description": "Net zero", "target_year": 2050}]
    },
    "data_quality_score": 75
}

try:
    print("Generating simple report...")
    
    # Temporarily modify the function to skip pretty printing
    import app.api.v1.endpoints.esrs_e1_full as esrs_module
    
    # Monkey patch to skip minidom parsing
    original_func = esrs_module.generate_world_class_esrs_e1_ixbrl
    
    def patched_func(data):
        result = {}
        try:
            # Call original up to XML generation
            import xml.etree.ElementTree as ET
            from datetime import datetime
            
            doc_id = f"ESRS-E1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            timestamp = datetime.now()
            
            # Generate the structure
            root = esrs_module.create_enhanced_ixbrl_structure(data, doc_id, timestamp)
            
            # Convert to string without pretty printing
            xml_str = ET.tostring(root, encoding='unicode')
            
            # Save raw XML
            filename = f"raw_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            with open(filename, 'w') as f:
                f.write(xml_str)
            
            print(f"✓ Generated raw XML: {filename}")
            
            # Try to create simple HTML wrapper
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>ESRS E1 Report - {data.get('organization', 'Unknown')}</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>ESRS E1 Climate Disclosure</h1>
    <h2>{data.get('organization', 'Unknown')} - {data.get('reporting_period', 'Unknown')}</h2>
    <div class="xbrl-content">
        {xml_str}
    </div>
</body>
</html>"""
            
            html_filename = f"simple_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(html_filename, 'w') as f:
                f.write(html)
            
            print(f"✓ Generated HTML: {html_filename}")
            
            result = {
                'ixbrl_content': xml_str,
                'report_html': html,
                'metadata': json.dumps({
                    'doc_id': doc_id,
                    'generated_at': timestamp.isoformat(),
                    'status': 'success'
                })
            }
            
        except Exception as e:
            print(f"Error in generation: {e}")
            raise
        
        return result
    
    # Use patched version
    result = patched_func(test_data)
    
    print("\n✅ SUCCESS! Report generated!")
    print("Check the generated files:")
    print("  - raw_report_*.xml")
    print("  - simple_report_*.html")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
