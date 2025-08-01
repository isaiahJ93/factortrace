#!/usr/bin/env python3
import re

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find and replace the extract_boundary_changes function
old_extract_pattern = r'def extract_boundary_changes\(data\):.*?return \{[^}]+\}'
new_extract_function = '''def extract_boundary_changes(data):
    """Extract boundary changes information from reporting data"""
    boundary_info = data.get('boundary_changes', {})
    changes_list = []
    
    # Check if there are any changes reported
    changes_from_previous = boundary_info.get('changes_from_previous', {})
    
    # Add entities added
    for entity in changes_from_previous.get('entities_added', []):
        changes_list.append({
            'date': data.get('reporting_period', '2024') + '-01-01',
            'description': f'Added entity: {entity}',
            'type': 'addition',
            'emissions_impact': boundary_info.get('impact_assessment', {}).get('emissions_impact', 0),
            'restatement_required': True,
            'restatement_completed': boundary_info.get('restatement_completed', False)
        })
    
    # Add entities removed
    for entity in changes_from_previous.get('entities_removed', []):
        changes_list.append({
            'date': data.get('reporting_period', '2024') + '-01-01',
            'description': f'Removed entity: {entity}',
            'type': 'removal',
            'emissions_impact': -abs(boundary_info.get('impact_assessment', {}).get('emissions_impact', 0)),
            'restatement_required': True,
            'restatement_completed': boundary_info.get('restatement_completed', False)
        })
    
    # Add methodology changes
    for change in changes_from_previous.get('methodology_changes', []):
        changes_list.append({
            'date': data.get('reporting_period', '2024') + '-01-01',
            'description': f'Methodology change: {change}',
            'type': 'methodology',
            'emissions_impact': 0,
            'restatement_required': True,
            'restatement_completed': boundary_info.get('restatement_completed', False)
        })
    
    # If no specific changes but has_changes is true, add a generic entry
    if changes_from_previous.get('has_changes', False) and not changes_list:
        changes_list.append({
            'date': data.get('reporting_period', '2024') + '-01-01',
            'description': 'Boundary changes occurred',
            'type': 'other',
            'emissions_impact': boundary_info.get('impact_assessment', {}).get('emissions_impact', 0),
            'restatement_required': True,
            'restatement_completed': boundary_info.get('restatement_completed', False)
        })
    
    return changes_list'''

# Replace the function
content = re.sub(old_extract_pattern, new_extract_function, content, flags=re.DOTALL)

# Save the file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Fixed extract_boundary_changes to return list format")
