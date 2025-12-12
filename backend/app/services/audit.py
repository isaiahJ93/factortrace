# app/services/audit.py
"""
Audit logging service for CSRD compliance.

Provides functions to log all CRUD operations on tenant-owned entities.
This creates an immutable audit trail required for regulatory compliance.

Usage:
    from app.services.audit import log_action, log_create, log_update, log_delete

    # In your endpoint:
    log_create(db, emission, current_user, request)
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Request
import logging

from app.models.audit import AuditLog, AuditAction

logger = logging.getLogger(__name__)


def _get_entity_type(entity: Any) -> str:
    """Get the class name of an entity."""
    return entity.__class__.__name__


def _compute_changes(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Compute the difference between old and new data.

    Returns a dict of changed fields with their old and new values.
    Only includes fields that actually changed.
    """
    changes = {}

    # Get all keys from both dicts
    all_keys = set(old_data.keys()) | set(new_data.keys())

    for key in all_keys:
        old_val = old_data.get(key)
        new_val = new_data.get(key)

        # Skip if values are equal
        if old_val == new_val:
            continue

        # Skip internal/system fields
        if key in ('updated_at', '_sa_instance_state'):
            continue

        changes[key] = {
            "old": _serialize_value(old_val),
            "new": _serialize_value(new_val)
        }

    return changes


def _serialize_value(value: Any) -> Any:
    """Serialize a value for JSON storage."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, 'value'):  # Enum
        return value.value
    if hasattr(value, '__dict__'):  # Complex object
        return str(value)
    return value


def _entity_to_dict(entity: Any) -> Dict[str, Any]:
    """Convert an entity to a dictionary for change tracking."""
    if entity is None:
        return {}

    result = {}
    for column in entity.__table__.columns:
        key = column.name
        value = getattr(entity, key, None)
        result[key] = _serialize_value(value)

    return result


def _extract_request_context(request: Optional[Request]) -> Dict[str, Optional[str]]:
    """Extract IP address and user agent from request."""
    if request is None:
        return {"ip_address": None, "user_agent": None}

    # Get IP address (handle proxies)
    ip_address = None
    if hasattr(request, 'headers'):
        ip_address = request.headers.get('x-forwarded-for')
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        else:
            ip_address = request.headers.get('x-real-ip')

    if not ip_address and hasattr(request, 'client') and request.client:
        ip_address = request.client.host

    # Get user agent
    user_agent = None
    if hasattr(request, 'headers'):
        user_agent = request.headers.get('user-agent')
        if user_agent and len(user_agent) > 500:
            user_agent = user_agent[:500]

    return {"ip_address": ip_address, "user_agent": user_agent}


def log_action(
    db: Session,
    action: AuditAction,
    entity: Any,
    tenant_id: str,
    user_id: Optional[int] = None,
    changes: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """
    Log an audit action.

    Args:
        db: Database session
        action: The action type (CREATE, UPDATE, DELETE, RESTORE)
        entity: The entity being modified
        tenant_id: The tenant ID
        user_id: The user ID performing the action (optional for system actions)
        changes: Dictionary of changes (for UPDATE actions)
        request: FastAPI request object for IP/user-agent extraction

    Returns:
        The created AuditLog record
    """
    request_context = _extract_request_context(request)

    audit_log = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        entity_type=_get_entity_type(entity),
        entity_id=entity.id,
        action=action.value,
        changes=changes,
        ip_address=request_context["ip_address"],
        user_agent=request_context["user_agent"]
    )

    db.add(audit_log)
    # Note: Don't commit here - let the caller commit with the main transaction

    logger.info(
        f"Audit: {action.value} {_get_entity_type(entity)}:{entity.id} "
        f"by user {user_id} in tenant {tenant_id}"
    )

    return audit_log


def log_create(
    db: Session,
    entity: Any,
    tenant_id: str,
    user_id: Optional[int] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """
    Log a CREATE action.

    Call after creating an entity (entity must have an id).
    """
    # For CREATE, store the full entity data as "changes"
    entity_data = _entity_to_dict(entity)
    changes = {
        key: {"old": None, "new": value}
        for key, value in entity_data.items()
        if value is not None
    }

    return log_action(
        db=db,
        action=AuditAction.CREATE,
        entity=entity,
        tenant_id=tenant_id,
        user_id=user_id,
        changes=changes,
        request=request
    )


def log_update(
    db: Session,
    entity: Any,
    old_data: Dict[str, Any],
    tenant_id: str,
    user_id: Optional[int] = None,
    request: Optional[Request] = None
) -> Optional[AuditLog]:
    """
    Log an UPDATE action.

    Args:
        entity: The updated entity
        old_data: Dictionary of old values (captured BEFORE the update)

    Returns:
        AuditLog if there were changes, None otherwise
    """
    new_data = _entity_to_dict(entity)
    changes = _compute_changes(old_data, new_data)

    # Don't log if nothing actually changed
    if not changes:
        logger.debug(f"No changes detected for {_get_entity_type(entity)}:{entity.id}")
        return None

    return log_action(
        db=db,
        action=AuditAction.UPDATE,
        entity=entity,
        tenant_id=tenant_id,
        user_id=user_id,
        changes=changes,
        request=request
    )


def log_delete(
    db: Session,
    entity: Any,
    tenant_id: str,
    user_id: Optional[int] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """
    Log a DELETE (soft delete) action.

    Call after soft-deleting an entity.
    """
    # For DELETE, store deleted_at change
    changes = {
        "deleted_at": {
            "old": None,
            "new": _serialize_value(getattr(entity, 'deleted_at', None))
        }
    }

    return log_action(
        db=db,
        action=AuditAction.DELETE,
        entity=entity,
        tenant_id=tenant_id,
        user_id=user_id,
        changes=changes,
        request=request
    )


def log_restore(
    db: Session,
    entity: Any,
    tenant_id: str,
    user_id: Optional[int] = None,
    request: Optional[Request] = None
) -> AuditLog:
    """
    Log a RESTORE action.

    Call after restoring a soft-deleted entity.
    """
    changes = {
        "deleted_at": {
            "old": "was_deleted",  # We don't know the exact timestamp
            "new": None
        }
    }

    return log_action(
        db=db,
        action=AuditAction.RESTORE,
        entity=entity,
        tenant_id=tenant_id,
        user_id=user_id,
        changes=changes,
        request=request
    )


def get_entity_audit_trail(
    db: Session,
    entity_type: str,
    entity_id: int,
    tenant_id: str,
    limit: int = 100
) -> list:
    """
    Get the audit trail for a specific entity.

    Returns audit logs in reverse chronological order (newest first).
    """
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )


def get_tenant_audit_log(
    db: Session,
    tenant_id: str,
    entity_type: Optional[str] = None,
    action: Optional[AuditAction] = None,
    user_id: Optional[int] = None,
    since: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> list:
    """
    Get audit logs for a tenant with optional filtering.

    Args:
        tenant_id: The tenant ID (required)
        entity_type: Filter by entity type (e.g., "Emission")
        action: Filter by action type
        user_id: Filter by user who performed action
        since: Only return logs after this datetime
        limit: Maximum number of records
        offset: Skip this many records (for pagination)

    Returns:
        List of AuditLog records, newest first
    """
    query = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    if action:
        query = query.filter(AuditLog.action == action.value)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if since:
        query = query.filter(AuditLog.created_at >= since)

    return (
        query
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


# Backwards compatibility for existing code
def create_audit_entry(data: dict) -> dict:
    """Legacy function for backwards compatibility."""
    return {
        "event": "Audit Entry Created",
        "data": data,
    }
