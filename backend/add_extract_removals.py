with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    lines = f.readlines()

# Find a good place to add the function (after other extract functions)
insert_pos = None
for i, line in enumerate(lines):
    if 'def extract_transition_plan_data' in line:
        # Find the end of this function
        j = i + 1
        while j < len(lines) and not lines[j].startswith('def '):
            j += 1
        insert_pos = j
        break

if insert_pos is None:
    # Fallback: add before create_e1_7_removals_offsets
    for i, line in enumerate(lines):
        if 'def create_e1_7_removals_offsets' in line:
            insert_pos = i
            break

# Add the missing function
new_function = '''
def extract_removals_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract GHG removals and carbon credits data"""
    removals = data.get('removals', {})
    
    return {
        'ghg_removals': removals.get('ghg_removals', 0),
        'removal_methods': removals.get('methods', []),
        'removal_verification': removals.get('verification', ''),
        'carbon_credits': removals.get('carbon_credits', {
            'cancelled': 0,
            'purchased': 0,
            'sold': 0,
            'net_position': 0
        }),
        'offsets_used': removals.get('offsets_used', 0),
        'removal_targets': removals.get('targets', []),
        'has_removals': removals.get('ghg_removals', 0) > 0
    }

'''

if insert_pos:
    lines.insert(insert_pos, new_function)
    print(f"✅ Added extract_removals_data at line {insert_pos}")

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.writelines(lines)
