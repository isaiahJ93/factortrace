# Find lines with organization_id and wrap them in hasattr checks
# Line ~585:
if hasattr(Emission, 'organization_id') and hasattr(current_user, 'organization_id'):
    query = query.filter(Emission.organization_id == current_user.organization_id)

# Line ~848:
if hasattr(Emission, 'organization_id') and hasattr(current_user, 'organization_id'):
    query = query.filter(Emission.organization_id == current_user.organization_id)
