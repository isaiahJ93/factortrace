#!/usr/bin/env python3
"""
Fix empty XBRL names in ESRS generator by replacing with proper values or removing XBRL wrapper
"""

import re

def fix_empty_xbrl_names():
    """Fix all empty name attributes in create_enhanced_xbrl_tag calls"""
    
    file_path = "/Users/isaiah/Documents/Scope3Tool/backend/app/api/v1/endpoints/esrs_e1_full.py"
    output_path = file_path.replace('.py', '_fixed.py')
    
    print("=== FIXING EMPTY XBRL NAMES ===")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes = []
    
    # Define replacements for empty names based on context
    # These should either be proper ESRS taxonomy names or the calls should be removed
    empty_name_fixes = [
        # Governance section
        {
            'context': 'Board oversight of climate-related risks',
            'old_pattern': r'create_enhanced_xbrl_tag\(\s*p_board,\s*\'nonNumeric\',\s*"",\s*\'c-current\',\s*\'Yes\' if gov_data\.get\(\'board_oversight\', False\) else \'No\',\s*xml_lang=\'en\'\s*\)',
            'new_code': '''# Fixed: Board oversight as plain text (no standard ESRS element)
    span = ET.SubElement(p_board, 'span')
    span.text = 'Yes' if gov_data.get('board_oversight', False) else 'No' '''
        },
        {
            'context': 'Board meetings discussing climate',
            'old_pattern': r'create_enhanced_xbrl_tag\(\s*p_meetings,\s*\'nonFraction\',\s*"",\s*\'c-current\',\s*gov_data\[\'board_meetings_climate\'\],\s*decimals=\'0\'\s*\)',
            'new_code': '''# Fixed: Board meetings as plain text
    span = ET.SubElement(p_meetings, 'span')
    span.text = str(gov_data['board_meetings_climate'])'''
        },
        {
            'context': 'Executive management responsibility',
            'old_pattern': r'create_enhanced_xbrl_tag\(\s*p_mgmt,\s*\'nonNumeric\',\s*"",\s*\'c-current\',\s*\'Yes\' if gov_data\.get\(\'management_responsibility\', False\) else \'No\',\s*xml_lang=\'en\'\s*\)',
            'new_code': '''# Fixed: Management responsibility as plain text
    span = ET.SubElement(p_mgmt, 'span')
    span.text = 'Yes' if gov_data.get('management_responsibility', False) else 'No' '''
        },
        {
            'context': 'Climate impact materiality',
            'old_pattern': r'create_enhanced_xbrl_tag\(\s*p_impact,\s*\'nonNumeric\',\s*"",\s*\'c-current\',\s*\'Material\' if mat_data\.get\(\'impact_material\', True\) else \'Not Material\',\s*xml_lang=\'en\'\s*\)',
            'new_code': '''# Fixed: Use proper ESRS materiality element
    create_enhanced_xbrl_tag(
        p_impact,
        'nonNumeric',
        'esrs:EnvironmentalImpactMateriality',
        'c-current',
        'true' if mat_data.get('impact_material', True) else 'false',
        xml_lang='en'
    )'''
        },
        {
            'context': 'Financial materiality',
            'old_pattern': r'create_enhanced_xbrl_tag\(\s*p_financial,\s*\'nonNumeric\',\s*"",\s*\'c-current\',\s*\'Material\' if mat_data\.get\(\'financial_material\', True\) else \'Not Material\',\s*xml_lang=\'en\'\s*\)',
            'new_code': '''# Fixed: Use proper ESRS materiality element
    create_enhanced_xbrl_tag(
        p_financial,
        'nonNumeric',
        'esrs:FinancialImpactMateriality',
        'c-current',
        'true' if mat_data.get('financial_material', True) else 'false',
        xml_lang='en'
    )'''
        }
    ]
    
    # Apply fixes
    for fix in empty_name_fixes:
        if re.search(fix['old_pattern'], content, re.MULTILINE | re.DOTALL):
            content = re.sub(
                fix['old_pattern'],
                fix['new_code'],
                content,
                flags=re.MULTILINE | re.DOTALL
            )
            fixes.append(fix['context'])
            print(f"✅ Fixed: {fix['context']}")
    
    # Find any remaining empty name calls using a more general pattern
    remaining_pattern = r'create_enhanced_xbrl_tag\([^)]*?""\s*,[^)]*?\)'
    remaining = re.findall(remaining_pattern, content, re.MULTILINE | re.DOTALL)
    
    if remaining:
        print(f"\n⚠️  Found {len(remaining)} more empty name calls that need manual review")
        
        # Replace them with a comment for manual review
        def replace_remaining(match):
            return f"# TODO: Fix empty XBRL name\n    # {match.group(0)}"
        
        content = re.sub(remaining_pattern, replace_remaining, content, flags=re.MULTILINE | re.DOTALL)
    
    # Add safety check to create_enhanced_xbrl_tag function
    print("\n2. Adding safety check to create_enhanced_xbrl_tag...")
    
    # Find the function and add check after docstring
    func_pattern = r'(def create_enhanced_xbrl_tag\([^)]+\):\s*"""[^"]*"""\s*)'
    
    def add_safety_check(match):
        return match.group(1) + '''
    # Safety check: Prevent empty name attributes
    if not name or str(name).strip() == '':
        # Log warning and return without creating XBRL element
        print(f"WARNING: Attempted to create XBRL tag with empty name. Value: {value}")
        # Add value as plain text instead
        if hasattr(parent, 'text') and parent.text:
            parent.text += str(value) if value is not None else ''
        else:
            span = ET.SubElement(parent, 'span')
            span.text = str(value) if value is not None else ''
        return None
    '''
    
    content = re.sub(func_pattern, add_safety_check, content, count=2)  # Apply to both functions
    
    # Fix duplicate HTML creation in create_enhanced_ixbrl_structure
    print("\n3. Fixing duplicate HTML creation...")
    
    # Comment out the duplicate HTML creation
    content = re.sub(
        r'(def create_enhanced_ixbrl_structure.*?)(root = ET\.Element\(\'html\')',
        r'\1# DUPLICATE HTML REMOVED - this should be merged with main generation\n    # \2',
        content,
        flags=re.DOTALL
    )
    
    # Write fixed file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Fixed {len(fixes)} empty name issues")
    print(f"✅ Saved to: {output_path}")
    
    # Create test script
    create_test_script(output_path)
    
    return output_path

def create_test_script(fixed_file_path):
    """Create a test script for the fixed generator"""
    
    test_script = f'''#!/usr/bin/env python3
"""Test the fixed ESRS generator"""

import sys
import os

# Add backend to path
sys.path.insert(0, '/Users/isaiah/Documents/Scope3Tool/backend')

# Import from fixed file
module_name = os.path.basename('{fixed_file_path}').replace('.py', '')
exec(f"from app.api.v1.endpoints.{{module_name}} import generate_xbrl_report")

# Test data
test_data = {{
    'organization': 'Test Corp',
    'entity_name': 'Test Corp',
    'lei': 'TEST123456789012345',
    'reporting_period': 2025,
    'governance': {{
        'board_oversight': True,
        'management_responsibility': True,
        'board_meetings_climate': 4,
        'climate_expertise': True
    }},
    'materiality': {{
        'impact_material': True,
        'financial_material': True
    }},
    'emissions': {{
        'scope1': 100,
        'scope2_location': 200,
        'scope3': 300
    }},
    'energy': {{
        'fossil': 1000,
        'renewable': 500
    }}
}}

print("Generating XBRL report...")
try:
    report = generate_xbrl_report(test_data)
    
    # Save output
    output_file = 'test_fixed_final.xhtml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Analyze output
    print(f"\\n✅ Generated {{output_file}}")
    print(f"File size: {{len(report)}} bytes")
    print(f"<head> tags: {{report.count('<head>')}}")
    print(f"<html> tags: {{report.count('<html')}}")  
    print(f"Empty names: {{report.count('name=\"\"')}}")
    print(f"Proper emission facts: {{report.count('esrs:Gross')}}")
    
    # Check for issues
    issues = []
    if report.count('<head>') > 1:
        issues.append("Multiple <head> tags")
    if report.count('name=""') > 0:
        issues.append("Empty name attributes")
    if report.count('<html') > 1:
        issues.append("Multiple <html> tags")
        
    if issues:
        print(f"\\n❌ Issues found: {{', '.join(issues)}}")
    else:
        print("\\n✅ No structural issues found!")
        
    print(f"\\nValidate with: poetry run arelleCmdLine --file {{output_file}} --validate")
    
except Exception as e:
    print(f"❌ Error: {{e}}")
    import traceback
    traceback.print_exc()
'''
    
    with open('test_fixed_final.py', 'w') as f:
        f.write(test_script)
    
    os.chmod('test_fixed_final.py', 0o755)
    print("✅ Created test_fixed_final.py")

if __name__ == "__main__":
    fix_empty_xbrl_names()