import sys
sys.path.append('.')

# Directly test the iXBRL structure creation
from app.api.v1.endpoints.esrs_e1_full import create_enhanced_ixbrl_structure
from datetime import datetime
import xml.etree.ElementTree as ET

# Minimal data that should work with the iXBRL creation
test_data = {
    "organization": "Test Company Ltd",
    "lei": "5493000KJTIIGC8Y1R12",
    "reporting_period": 2024,
    "emissions": {
        "scope1": 1000,
        "scope2_location": 500,
        "scope2_market": 400
    },
    "scope3_detailed": {
        f"category_{i}": {
            "emissions_tco2e": 100 * i,
            "excluded": False
        } for i in range(1, 16)
    },
    "transition_plan": {
        "adopted": True,
        "net_zero_target_year": 2050
    },
    "governance": {
        "board_oversight": True
    },
    "data_quality_score": 75
}

try:
    print("Testing direct iXBRL structure creation...")
    
    # Create the iXBRL structure directly
    doc_id = "TEST-001"
    timestamp = datetime.now()
    
    # Check if the function exists
    print(f"Function exists: {callable(create_enhanced_ixbrl_structure)}")
    
    # Try to create the structure
    root = create_enhanced_ixbrl_structure(test_data, doc_id, timestamp)
    
    print("✓ iXBRL structure created successfully!")
    
    # Convert to string
    from xml.dom import minidom
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Save to file
    with open('test_ixbrl_output.xbrl', 'w') as f:
        f.write(pretty_xml)
    
    print("✓ Saved to test_ixbrl_output.xbrl")
    print(f"File size: {len(pretty_xml)} characters")
    
    # Show first 500 characters
    print("\nFirst 500 characters of output:")
    print(pretty_xml[:500])
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
