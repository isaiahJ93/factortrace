with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find a good place to add extraction functions (after other extract functions)
insert_pos = None
for i, line in enumerate(lines):
    if 'def extract_financial_effects_data' in line:
        # Find the end of this function
        j = i + 1
        while j < len(lines) and not lines[j].startswith('def '):
            j += 1
        insert_pos = j
        break

if insert_pos is None:
    # Fallback: add before create_e1_1_transition_plan
    for i, line in enumerate(lines):
        if 'def create_e1_1_transition_plan' in line:
            insert_pos = i
            break

# Add the missing extraction functions
new_functions = '''
def extract_transition_plan_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract transition plan data for ESRS E1-1"""
    transition_plan = data.get('transition_plan', {})
    
    return {
        'has_transition_plan': transition_plan.get('exists', False),
        'plan_description': transition_plan.get('description', ''),
        'targets': transition_plan.get('targets', []),
        'milestones': transition_plan.get('milestones', []),
        'implementation_status': transition_plan.get('implementation_status', 'Not started'),
        'governance': transition_plan.get('governance', {}),
        'funding': transition_plan.get('funding', {}),
        'key_actions': transition_plan.get('key_actions', []),
        'alignment_with_eu_goals': transition_plan.get('alignment_with_eu_goals', False),
        'climate_neutrality_target': transition_plan.get('climate_neutrality_target', '2050')
    }

'''

if insert_pos:
    lines.insert(insert_pos, new_functions)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)

print(f"✅ Added extract_transition_plan_data at line {insert_pos}")
