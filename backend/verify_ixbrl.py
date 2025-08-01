#!/usr/bin/env python3
"""
Verify that generated XHTML files contain proper iXBRL tags
"""

import os
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def verify_ixbrl_file(filepath: str) -> dict:
    """Verify iXBRL compliance of a file"""
    results = {
        "filename": filepath,
        "valid_xml": False,
        "has_namespaces": False,
        "has_contexts": False,
        "has_units": False,
        "has_numeric_facts": False,
        "has_text_facts": False,
        "fact_count": 0,
        "issues": []
    }
    
    try:
        # Parse the file
        tree = ET.parse(filepath)
        root = tree.getroot()
        results["valid_xml"] = True
        
        # Check namespaces
        namespaces = {
            'ix': 'http://www.xbrl.org/2013/inlineXBRL',
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'xhtml': 'http://www.w3.org/1999/xhtml'
        }
        
        # Check if namespaces are declared
        root_attribs = root.attrib
        for prefix, uri in namespaces.items():
            if f'xmlns:{prefix}' in root_attrib.keys():
                if root_attrib[f'xmlns:{prefix}'] == uri:
                    results["has_namespaces"] = True
                    break
        
        # Check for contexts
        contexts = root.findall('.//{http://www.xbrl.org/2003/instance}context')
        if contexts:
            results["has_contexts"] = True
            print(f"✅ Found {len(contexts)} contexts")
        else:
            results["issues"].append("No xbrli:context elements found")
        
        # Check for units
        units = root.findall('.//{http://www.xbrl.org/2003/instance}unit')
        if units:
            results["has_units"] = True
            print(f"✅ Found {len(units)} units")
        else:
            results["issues"].append("No xbrli:unit elements found")
        
        # Check for numeric facts
        numeric_facts = root.findall('.//{http://www.xbrl.org/2013/inlineXBRL}nonFraction')
        if numeric_facts:
            results["has_numeric_facts"] = True
            results["fact_count"] += len(numeric_facts)
            print(f"✅ Found {len(numeric_facts)} numeric facts (ix:nonFraction)")
            
            # Verify each numeric fact
            for fact in numeric_facts[:5]:  # Check first 5
                name = fact.get('name', 'unnamed')
                context = fact.get('contextRef', 'no-context')
                unit = fact.get('unitRef', 'no-unit')
                value = fact.text or 'no-value'
                print(f"   - {name}: {value} (context: {context}, unit: {unit})")
        else:
            results["issues"].append("No ix:nonFraction elements found")
        
        # Check for text facts
        text_facts = root.findall('.//{http://www.xbrl.org/2013/inlineXBRL}nonNumeric')
        if text_facts:
            results["has_text_facts"] = True
            results["fact_count"] += len(text_facts)
            print(f"✅ Found {len(text_facts)} text facts (ix:nonNumeric)")
            
            for fact in text_facts[:3]:  # Check first 3
                name = fact.get('name', 'unnamed')
                context = fact.get('contextRef', 'no-context')
                value = (fact.text or 'no-value')[:50] + '...' if len(fact.text or '') > 50 else fact.text
                print(f"   - {name}: {value} (context: {context})")
        else:
            results["issues"].append("No ix:nonNumeric elements found")
        
        # Check for hidden section
        hidden = root.find('.//{http://www.xbrl.org/2013/inlineXBRL}hidden')
        if hidden:
            print("✅ Found ix:hidden section")
        else:
            results["issues"].append("No ix:hidden section found")
        
        # Check for references to contexts and units
        all_elements = root.findall('.//*[@contextRef]')
        context_refs = set(elem.get('contextRef') for elem in all_elements)
        print(f"\n📊 Context references used: {context_refs}")
        
        all_elements = root.findall('.//*[@unitRef]')
        unit_refs = set(elem.get('unitRef') for elem in all_elements)
        print(f"📊 Unit references used: {unit_refs}")
        
    except ET.ParseError as e:
        results["issues"].append(f"XML Parse Error: {e}")
    except Exception as e:
        results["issues"].append(f"Error: {e}")
    
    return results

def find_xhtml_files():
    """Find all XHTML files in current directory"""
    files = []
    for pattern in ['*.xhtml', '*.html']:
        files.extend(Path('.').glob(pattern))
    
    # Filter to likely ESRS files
    esrs_files = [f for f in files if 'esrs' in str(f).lower()]
    return esrs_files

def main():
    print("🔍 iXBRL Verification Tool")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        # Verify specific file
        filepath = sys.argv[1]
        if os.path.exists(filepath):
            print(f"\nVerifying: {filepath}")
            results = verify_ixbrl_file(filepath)
        else:
            print(f"❌ File not found: {filepath}")
            return
    else:
        # Find and verify all ESRS files
        files = find_xhtml_files()
        if not files:
            print("❌ No XHTML files found!")
            return
        
        print(f"\nFound {len(files)} ESRS XHTML files")
        
        # Get the most recent one
        latest_file = max(files, key=os.path.getmtime)
        print(f"\nVerifying most recent: {latest_file}")
        results = verify_ixbrl_file(str(latest_file))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY:")
    print(f"✓ Valid XML: {results['valid_xml']}")
    print(f"✓ Has namespaces: {results['has_namespaces']}")
    print(f"✓ Has contexts: {results['has_contexts']}")
    print(f"✓ Has units: {results['has_units']}")
    print(f"✓ Has numeric facts: {results['has_numeric_facts']}")
    print(f"✓ Has text facts: {results['has_text_facts']}")
    print(f"✓ Total facts: {results['fact_count']}")
    
    if results['issues']:
        print("\n⚠️  ISSUES FOUND:")
        for issue in results['issues']:
            print(f"  - {issue}")
    else:
        print("\n✅ No issues found!")
    
    # Compliance check
    is_compliant = (
        results['valid_xml'] and 
        results['has_contexts'] and 
        results['has_units'] and 
        (results['has_numeric_facts'] or results['has_text_facts'])
    )
    
    print(f"\n🏁 iXBRL Compliant: {'YES ✅' if is_compliant else 'NO ❌'}")

if __name__ == "__main__":
    main()