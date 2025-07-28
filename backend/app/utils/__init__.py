def _coerce(value):
    """Simple coerce function - customize as needed"""
    if value is None:
        return None
    return str(value)