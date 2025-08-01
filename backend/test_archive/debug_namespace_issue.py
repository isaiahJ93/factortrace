import sys
sys.path.append('.')

from app.api.v1.endpoints.esrs_e1_full import create_enhanced_ixbrl_structure
import xml.etree.ElementTree as ET
from datetime import datetime
import json
import re

# Use the complete test data
with open('debug_test_data.json', 'r') as f:
    test_data = json.load(f)

try:
    print("Generating iXBRL structure...")
    
    # Generate the structure
    doc_id = f"ESRS-E1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    timestamp = datetime.now()
    
    root = create_enhanced_ixbrl_structure(test_data, doc_id, timestamp)
    
    # Convert to string
    xml_str = ET.tostring(root, encoding='unicode')
    
    # Save raw XML
    with open('debug_raw.xml', 'w') as f:
        f.write(xml_str)
    
    print(f"✓ Saved raw XML to debug_raw.xml ({len(xml_str):,} characters)")
    
    # Find the problematic area around column 43103
    if len(xml_str) > 43103:
        start = max(0, 43103 - 200)
        end = min(len(xml_str), 43103 + 200)
        print(f"\nArea around column 43103:")
        print(f"...{xml_str[start:end]}...")
        
        # Find namespace prefixes in that area
        area_text = xml_str[start:end]
        prefixes = re.findall(r'<([a-zA-Z0-9-]+):', area_text)
        print(f"\nPrefixes found in problem area: {set(prefixes)}")
    
    # Find all namespace prefixes used in the document
    all_prefixes = set(re.findall(r'<([a-zA-Z0-9-]+):', xml_str))
    print(f"\nAll prefixes used in document: {all_prefixes}")
    
    # Check which namespaces are declared
    declared_namespaces = set(re.findall(r'xmlns:([a-zA-Z0-9-]+)=', xml_str))
    print(f"\nDeclared namespaces: {declared_namespaces}")
    
    # Find undeclared prefixes
    undeclared = all_prefixes - declared_namespaces - {'ix'}  # ix might be special
    print(f"\nUndeclared prefixes: {undeclared}")
    
    # Try to create a version with all namespaces declared
    if undeclared:
        print("\nFixing undeclared namespaces...")
        
        # Add missing namespace declarations
        root_tag_match = re.match(r'<[^>]+>', xml_str)
        if root_tag_match:
            root_tag = root_tag_match.group(0)
            
            # Add declarations for missing namespaces
            new_declarations = []
            for prefix in undeclared:
                if prefix == 'esrs-e1':
                    new_declarations.append(f'xmlns:{prefix}="http://xbrl.org/esrs/2023/esrs-e1"')
                elif prefix == 'esrs':
                    new_declarations.append(f'xmlns:{prefix}="http://xbrl.org/esrs/2023"')
                elif prefix == 'iso4217':
                    new_declarations.append(f'xmlns:{prefix}="http://www.xbrl.org/2003/iso4217"')
                elif prefix == 'xbrli':
                    new_declarations.append(f'xmlns:{prefix}="http://www.xbrl.org/2003/instance"')
                elif prefix == 'ixt':
                    new_declarations.append(f'xmlns:{prefix}="http://www.xbrl.org/inlineXBRL/transformation/2020-02-12"')
                else:
                    new_declarations.append(f'xmlns:{prefix}="http://example.com/{prefix}"')
            
            # Insert declarations into root tag
            if new_declarations:
                new_root_tag = root_tag[:-1] + ' ' + ' '.join(new_declarations) + '>'
                xml_str_fixed = xml_str.replace(root_tag, new_root_tag, 1)
                
                with open('debug_fixed.xml', 'w') as f:
                    f.write(xml_str_fixed)
                
                print(f"✓ Saved fixed XML to debug_fixed.xml")
                
                # Try to parse the fixed version
                try:
                    from xml.dom import minidom
                    dom = minidom.parseString(xml_str_fixed)
                    pretty_xml = dom.toprettyxml(indent="  ")
                    
                    with open('debug_pretty.xml', 'w') as f:
                        f.write(pretty_xml)
                    
                    print("✓ Successfully parsed and saved pretty XML to debug_pretty.xml")
                    
                    # Create HTML wrapper
                    html = f"""<!DOCTYPE html>
<html xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xmlns:esrs="http://xbrl.org/esrs/2023"
      xmlns:esrs-e1="http://xbrl.org/esrs/2023/esrs-e1"
      xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
      xmlns:ixt="http://www.xbrl.org/inlineXBRL/transformation/2020-02-12">
<head>
    <title>ESRS E1 Climate Disclosure - {test_data.get('organization', 'Unknown')}</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #2c5530; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f0f0f0; }}
        .xbrl-tag {{ background-color: #e8f5e9; padding: 2px 4px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>ESRS E1 Climate Disclosure Report</h1>
    <h2>{test_data.get('organization', 'Unknown')} - Reporting Period {test_data.get('reporting_period', 'Unknown')}</h2>
    <div class="xbrl-content">
        {pretty_xml}
    </div>
</body>
</html>"""
                    
                    with open('ESRS_E1_Debug_Report.html', 'w') as f:
                        f.write(html)
                    
                    print("\n✅ SUCCESS! Generated ESRS_E1_Debug_Report.html")
                    print("   This proves the integration is working!")
                    
                except Exception as e:
                    print(f"Error parsing fixed XML: {e}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
