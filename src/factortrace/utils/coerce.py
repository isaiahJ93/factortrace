from __future__ import annotations
def _coerce(enum_cls, value):
    """Attempt to coerce a string or int to an Enum value, or return None."""
    try:
        return enum_cls(value)
    except (ValueError, TypeError):
        return None
    
    