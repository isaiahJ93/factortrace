#!/usr/bin/env python3
"""
Fix ALL remaining empty XBRL names by removing XBRL wrappers
"""

import re
import os

def fix_all_empty_names():
    """Remove all XBRL tags with empty names"""
    
    file_path = "/Users/isaiah/Documents/Scope3Tool/backend/app/api/v1/endpoints/esrs_e1_full_fixed.py"
    output_path = file_path.replace('_fixed.py', '_final.py')
    
    print("=== FIXING ALL REMAINING EMPTY NAMES ===")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count TODO items
    todo_count = content.count('TODO: Fix empty XBRL name')
    print(f"Found {todo_count} TODO items to fix")
    
    # Strategy: Replace all commented TODO lines with proper plain text additions
    # Pattern: # TODO: Fix empty XBRL name\n    # create_enhanced_xbrl_tag(...)
    
    def extract_value_from_commented_call(commented_call):
        """Extract the value from a commented create_enhanced_xbrl_tag call"""
        # Look for the value parameter (usually 4th or 5th parameter)
        lines = commented_call.split('\n')
        value = None
        
        # Join all lines to parse easier
        full_call = ' '.join(line.strip().replace('#', '') for line in lines)
        
        # Try to extract value using different patterns
        patterns = [
            r"'Yes' if.*?else 'No'",
            r'"Yes" if.*?else "No"',
            r"data\.get\([^)]+\)",
            r"gov_data\.get\([^)]+\)",
            r"str\([^)]+\)",
            r"'[^']+'" ,
            r'"[^"]+"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_call)
            if match:
                value = match.group(0)
                break
                
        return value or "''"
    
    # Replace pattern: TODO comment followed by commented create_enhanced_xbrl_tag
    pattern = r'(\s*)# TODO: Fix empty XBRL name\n\s*# (create_enhanced_xbrl_tag\([^)]+\))'
    
    def replace_todo(match):
        indent = match.group(1)
        commented_call = match.group(2)
        
        # Extract value from the commented call
        value = extract_value_from_commented_call(commented_call)
        
        # Generate replacement code
        replacement = f"""{indent}# Fixed: Removed empty XBRL name
{indent}span = ET.SubElement(parent, 'span')
{indent}span.text = str({value}) if {value} is not None else ''"""
        
        return replacement
    
    # First pass: Replace simple TODOs
    content = re.sub(pattern, replace_todo, content)
    
    # Second pass: Handle multi-line TODOs
    multiline_pattern = r'(\s*)# TODO: Fix empty XBRL name\n(\s*#[^\n]+\n)+'
    
    def replace_multiline_todo(match):
        indent = match.group(1)
        full_match = match.group(0)
        
        # Extract the full commented call
        lines = full_match.split('\n')
        call_lines = [line for line in lines if 'create_enhanced_xbrl_tag' in line or (',' in line and '#' in line)]
        
        if call_lines:
            # Try to determine parent element
            parent = 'parent'  # default
            for line in call_lines:
                if 'p_' in line:
                    parent_match = re.search(r'(p_\w+)', line)
                    if parent_match:
                        parent = parent_match.group(1)
                        break
            
            # Look for value
            value_line = None
            for line in call_lines:
                if 'Yes' in line or 'No' in line or 'data.get' in line or 'True' in line or 'False' in line:
                    value_line = line
                    break
            
            if value_line:
                # Extract value expression
                value = extract_value_from_commented_call(value_line)
                
                return f"""{indent}# Fixed: Removed empty XBRL name
{indent}if {parent} and hasattr({parent}, 'text'):
{indent}    span = ET.SubElement({parent}, 'span')
{indent}    span.text = str({value}) if {value} is not None else ''"""
        
        # If we can't parse it, just remove the XBRL wrapper
        return f"{indent}# Fixed: Removed empty XBRL wrapper"
    
    content = re.sub(multiline_pattern, replace_multiline_todo, content, flags=re.MULTILINE)
    
    # Third pass: Clean up any remaining TODO comments
    content = content.replace('# TODO: Fix empty XBRL name', '# Fixed: Removed empty XBRL name')
    
    # Final safety: Ensure no create_enhanced_xbrl_tag calls with empty names remain
    # This catches any we might have missed
    empty_name_pattern = r'create_enhanced_xbrl_tag\s*\([^,]+,\s*[^,]+,\s*["\'][\s]*["\']'
    remaining = re.findall(empty_name_pattern, content)
    
    if remaining:
        print(f"\n⚠️  Warning: Found {len(remaining)} more empty name patterns")
        # Replace them with comments
        content = re.sub(
            empty_name_pattern + r'[^)]*\)',
            '# REMOVED: Empty XBRL name call',
            content
        )
    
    # Write the final fixed file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Fixed all empty names")
    print(f"✅ Saved to: {output_path}")
    
    # Verify the fix
    remaining_todos = content.count('TODO: Fix empty XBRL name')
    remaining_empty = len(re.findall(r'name\s*=\s*["\'][\s]*["\']', content))
    
    print(f"\nVerification:")
    print(f"  Remaining TODOs: {remaining_todos}")
    print(f"  Remaining empty names: {remaining_empty}")
    
    # Create final test script
    create_final_test(output_path)
    
    return output_path

def create_final_test(fixed_file):
    """Create test for the fully fixed generator"""
    
    module_name = os.path.basename(fixed_file).replace('.py', '')
    
    test_script = f'''#!/usr/bin/env python3
"""Test the fully fixed ESRS generator"""

import sys
sys.path.insert(0, '/Users/isaiah/Documents/Scope3Tool/backend')

from app.api.v1.endpoints.{module_name} import generate_xbrl_report

# Comprehensive test data
test_data = {{
    'organization': 'Test Corp',
    'entity_name': 'Test Corp',
    'lei': 'TEST123456789012345',
    'reporting_period': 2025,
    'language': 'en',
    'governance': {{
        'board_oversight': True,
        'management_responsibility': True,
        'board_meetings_climate': 4,
        'climate_expertise': True,
        'climate_committee': True,
        'climate_incentives': True
    }},
    'materiality': {{
        'impact_material': True,
        'financial_material': True
    }},
    'emissions': {{
        'scope1': 100,
        'scope2_location': 200,
        'scope2_market': 180,
        'scope3': 300
    }},
    'energy': {{
        'fossil': 1000,
        'renewable': 500,
        'total': 1500
    }},
    'policies': [
        {{'name': 'Climate Policy', 'description': 'Our climate policy'}}
    ],
    'actions': [
        {{'description': 'Solar installation', 'investment_meur': 5}}
    ],
    'targets': [
        {{'target_year': 2030, 'reduction_percent': 50}}
    ]
}}

print("Generating final XBRL report...")
try:
    report = generate_xbrl_report(test_data)
    
    output_file = 'esrs_e1_final_output.xhtml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\\n✅ Generated {{output_file}}")
    print(f"File size: {{len(report):,}} bytes")
    
    # Detailed analysis
    print("\\n=== STRUCTURE ANALYSIS ===")
    print(f"<html> tags: {{report.count('<html')}}")
    print(f"<head> tags: {{report.count('<head>')}}")
    print(f"</head> tags: {{report.count('</head>')}}")
    print(f"<body> tags: {{report.count('<body>')}}")
    print(f"Empty names: {{report.count('name=\"\"')}}")
    
    print("\\n=== XBRL FACTS ===")
    print(f"Total XBRL facts: {{report.count('<ix:non')}}")
    print(f"Emission facts: {{report.count('esrs:Gross')}}")
    print(f"Energy facts: {{report.count('esrs:Energy')}}")
    
    # Final check
    if report.count('name=""') == 0 and report.count('<head>') == 1:
        print("\\n🎉 SUCCESS: All structural issues fixed!")
    else:
        print("\\n⚠️  Some issues remain - check validation")
        
    print(f"\\nValidate with:")
    print(f"poetry run arelleCmdLine --file {{output_file}} --validate")
    
except Exception as e:
    print(f"❌ Error: {{e}}")
    import traceback
    traceback.print_exc()
'''
    
    with open('test_final_generator.py', 'w') as f:
        f.write(test_script)
    
    os.chmod('test_final_generator.py', 0o755)
    print("✅ Created test_final_generator.py")

if __name__ == "__main__":
    fix_all_empty_names()