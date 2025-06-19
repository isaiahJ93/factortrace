from datetime import datetime
from factortrace.enums import AuditActionEnum
from factortrace.models.emissions_voucher import AuditEntry

def create_audit_entry(user_id, action: AuditActionEnum, field_changed=None, old_value=None, new_value=None, ip_address=None):
    return AuditEntry(
        timestamp=datetime.utcnow(),
        user_id=user_id,
        action=action,
        field_changed=field_changed,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address
    )

