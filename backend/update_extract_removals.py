with open('app/api/v1/endpoints/esrs_e1_full.py', 'r') as f:
    content = f.read()

# Find and update the extract_removals_data function
old_return = '''return {
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
    }'''

new_return = '''return {
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
        'has_removals': removals.get('ghg_removals', 0) > 0,
        'total_removals_tco2': removals.get('ghg_removals', 0),  # Added missing key
        'carbon_credits_cancelled': removals.get('carbon_credits', {}).get('cancelled', 0)
    }'''

content = content.replace(old_return, new_return)

with open('app/api/v1/endpoints/esrs_e1_full.py', 'w') as f:
    f.write(content)

print("✅ Updated extract_removals_data with missing keys")
