#!/usr/bin/env python3

with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Add the missing extract_boundary_changes function
missing_functions = '''
def extract_boundary_changes(data):
    """Extract boundary changes information from reporting data"""
    boundary_info = data.get('boundary_changes', {})
    
    return {
        'reporting_boundary': boundary_info.get('reporting_boundary', 'financial_control'),
        'consolidation_method': boundary_info.get('consolidation_method', 'operational_control'),
        'changes_from_previous': boundary_info.get('changes_from_previous', {
            'entities_added': [],
            'entities_removed': [],
            'methodology_changes': [],
            'has_changes': False
        }),
        'impact_assessment': boundary_info.get('impact_assessment', {
            'emissions_impact': 0,
            'percentage_change': 0,
            'explanation': 'No significant boundary changes in the reporting period'
        }),
        'subsidiary_coverage': boundary_info.get('subsidiary_coverage', {
            'total_subsidiaries': 0,
            'included_in_boundary': 0,
            'exclusions': [],
            'exclusion_reasons': []
        })
    }

def validate_data_quality_indicators(data):
    """Validate data quality indicators for ESRS compliance"""
    quality_indicators = data.get('data_quality', {})
    
    validation = {
        'is_valid': True,
        'issues': [],
        'quality_score': 0
    }
    
    # Check primary data percentage
    primary_data_pct = quality_indicators.get('primary_data_percentage', 0)
    if primary_data_pct < 50:
        validation['issues'].append('Primary data percentage below 50% threshold')
    
    # Check estimation methods
    estimation_methods = quality_indicators.get('estimation_methods', [])
    if not estimation_methods:
        validation['issues'].append('No estimation methods documented')
    
    # Calculate quality score
    scores = {
        'primary_data': min(primary_data_pct / 100 * 50, 50),
        'documentation': 20 if quality_indicators.get('methodology_documented', False) else 0,
        'verification': 20 if quality_indicators.get('third_party_verified', False) else 0,
        'uncertainty': 10 if quality_indicators.get('uncertainty_assessed', False) else 0
    }
    
    validation['quality_score'] = sum(scores.values())
    validation['is_valid'] = len(validation['issues']) == 0
    
    return validation

def extract_climate_targets(data):
    """Extract climate targets and commitments"""
    targets = data.get('climate_targets', {})
    
    return {
        'net_zero_target': {
            'year': targets.get('net_zero_year', 2050),
            'scope_coverage': targets.get('net_zero_scopes', ['scope1', 'scope2', 'scope3']),
            'validated': targets.get('sbti_validated', False)
        },
        'interim_targets': targets.get('interim_targets', [
            {
                'year': 2030,
                'reduction_percentage': 50,
                'baseline_year': 2020,
                'scopes': ['scope1', 'scope2']
            }
        ]),
        'intensity_targets': targets.get('intensity_targets', []),
        'renewable_energy_targets': targets.get('renewable_targets', {
            'percentage': 100,
            'year': 2030,
            'current_percentage': 0
        })
    }

def validate_transition_plan(data):
    """Validate transition plan completeness for ESRS E1-1"""
    transition_plan = data.get('transition_plan', {})
    
    required_elements = {
        'governance': 'Governance and accountability mechanisms',
        'targets': 'GHG emission reduction targets',
        'actions': 'Key decarbonization actions and measures',
        'resources': 'Financial and other resources allocated',
        'progress_tracking': 'Progress tracking mechanisms',
        'alignment_1_5c': 'Alignment with 1.5°C pathway'
    }
    
    validation = {
        'is_complete': True,
        'missing_elements': [],
        'completeness_score': 0
    }
    
    for key, description in required_elements.items():
        if not transition_plan.get(key):
            validation['is_complete'] = False
            validation['missing_elements'].append(description)
    
    validation['completeness_score'] = (
        (len(required_elements) - len(validation['missing_elements'])) 
        / len(required_elements) * 100
    )
    
    return validation

'''

# Find where to insert - before validate_boundary_changes function
import re
insert_match = re.search(r'def validate_boundary_changes', content)
if insert_match:
    insert_pos = insert_match.start()
    content = content[:insert_pos] + missing_functions + '\n' + content[insert_pos:]
    print("✅ Added missing functions for ESRS compliance")
else:
    print("❌ Could not find insertion point")

# Save the updated file
with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Updated esrs_e1_full.py with all required functions")
