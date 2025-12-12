# app/core/tenant.py
"""
Tenant isolation helper functions.

These utilities enforce multi-tenant data isolation across all queries.
Use these functions consistently to prevent cross-tenant data leaks.

Security: ALWAYS use these helpers instead of raw queries on tenant-owned models.
"""
from typing import TypeVar, Optional, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Session, Query
from fastapi import HTTPException, status

if TYPE_CHECKING:
    from app.schemas.auth import CurrentUser

# Generic type for SQLAlchemy models
T = TypeVar('T')


def _has_soft_delete(model: Any) -> bool:
    """Check if a model supports soft delete (has deleted_at column)."""
    return hasattr(model, 'deleted_at')


def tenant_filter(query: Query, model: Any, tenant_id: str) -> Query:
    """
    Apply tenant isolation filter to a query.

    ALWAYS use this function when querying tenant-owned data.

    Args:
        query: SQLAlchemy query object
        model: The model class being queried (must have tenant_id column)
        tenant_id: The tenant ID to filter by

    Returns:
        Query filtered by tenant_id

    Example:
        query = tenant_filter(db.query(Emission), Emission, current_user.tenant_id)
    """
    return query.filter(model.tenant_id == tenant_id)


def get_tenant_record(
    db: Session,
    model: Any,
    record_id: Any,
    tenant_id: str,
    raise_404: bool = True,
    include_deleted: bool = False
) -> Optional[Any]:
    """
    Get a single record with tenant isolation.

    Automatically excludes soft-deleted records unless include_deleted=True.

    Args:
        db: Database session
        model: The model class to query
        record_id: Primary key value
        tenant_id: The tenant ID to filter by
        raise_404: If True, raises HTTPException if not found
        include_deleted: If True, include soft-deleted records (default False)

    Returns:
        The record if found and belongs to tenant, else None

    Raises:
        HTTPException(404) if raise_404=True and record not found

    Example:
        emission = get_tenant_record(db, Emission, emission_id, current_user.tenant_id)
    """
    query = db.query(model).filter(
        model.id == record_id,
        model.tenant_id == tenant_id
    )

    # Exclude soft-deleted records by default
    if _has_soft_delete(model) and not include_deleted:
        query = query.filter(model.deleted_at.is_(None))

    record = query.first()

    if record is None and raise_404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} not found"
        )

    return record


def tenant_query(
    db: Session,
    model: Any,
    tenant_id: str,
    include_deleted: bool = False
) -> Query:
    """
    Create a tenant-scoped query.

    Convenience function that combines db.query() with tenant filtering.
    Automatically excludes soft-deleted records unless include_deleted=True.

    Args:
        db: Database session
        model: The model class to query
        tenant_id: The tenant ID to filter by
        include_deleted: If True, include soft-deleted records (default False)

    Returns:
        Query pre-filtered by tenant_id (and deleted_at IS NULL for soft-delete models)

    Example:
        emissions = tenant_query(db, Emission, current_user.tenant_id).all()
        # Include deleted:
        all_emissions = tenant_query(db, Emission, current_user.tenant_id, include_deleted=True).all()
    """
    query = db.query(model).filter(model.tenant_id == tenant_id)

    # Automatically exclude soft-deleted records
    if _has_soft_delete(model) and not include_deleted:
        query = query.filter(model.deleted_at.is_(None))

    return query


def create_tenant_record(
    db: Session,
    model: Any,
    tenant_id: str,
    **kwargs
) -> Any:
    """
    Create a new record with tenant_id automatically set.

    Args:
        db: Database session
        model: The model class to instantiate
        tenant_id: The tenant ID to set
        **kwargs: Additional fields for the model

    Returns:
        The created record (not yet committed)

    Example:
        emission = create_tenant_record(
            db, Emission, current_user.tenant_id,
            scope=1, category="electricity", amount=100.0
        )
        db.commit()
    """
    record = model(tenant_id=tenant_id, **kwargs)
    db.add(record)
    return record


def update_tenant_record(
    db: Session,
    model: Any,
    record_id: Any,
    tenant_id: str,
    update_data: dict,
    raise_404: bool = True
) -> Optional[Any]:
    """
    Update a record with tenant isolation check.

    Args:
        db: Database session
        model: The model class
        record_id: Primary key value
        tenant_id: The tenant ID to verify
        update_data: Dict of fields to update
        raise_404: If True, raises HTTPException if not found

    Returns:
        The updated record, or None if not found

    Raises:
        HTTPException(404) if raise_404=True and record not found

    Example:
        emission = update_tenant_record(
            db, Emission, emission_id, current_user.tenant_id,
            {"amount": 150.0, "notes": "Updated"}
        )
        db.commit()
    """
    record = get_tenant_record(db, model, record_id, tenant_id, raise_404)

    if record is None:
        return None

    # Prevent tenant_id from being changed via update
    update_data.pop('tenant_id', None)

    for key, value in update_data.items():
        if hasattr(record, key):
            setattr(record, key, value)

    return record


def delete_tenant_record(
    db: Session,
    model: Any,
    record_id: Any,
    tenant_id: str,
    raise_404: bool = True
) -> bool:
    """
    Hard delete a record with tenant isolation check.

    WARNING: Prefer soft_delete_tenant_record() for audit compliance.
    Use this only for non-auditable data or when required.

    Args:
        db: Database session
        model: The model class
        record_id: Primary key value
        tenant_id: The tenant ID to verify
        raise_404: If True, raises HTTPException if not found

    Returns:
        True if deleted, False if not found (when raise_404=False)

    Raises:
        HTTPException(404) if raise_404=True and record not found

    Example:
        delete_tenant_record(db, Emission, emission_id, current_user.tenant_id)
        db.commit()
    """
    result = db.query(model).filter(
        model.id == record_id,
        model.tenant_id == tenant_id
    ).delete()

    if result == 0 and raise_404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} not found"
        )

    return result > 0


def soft_delete_tenant_record(
    db: Session,
    model: Any,
    record_id: Any,
    tenant_id: str,
    raise_404: bool = True
) -> Optional[Any]:
    """
    Soft delete a record by setting deleted_at timestamp.

    This is the preferred delete method for CSRD compliance.
    Records are excluded from normal queries but remain in database.

    Args:
        db: Database session
        model: The model class (must have deleted_at column)
        record_id: Primary key value
        tenant_id: The tenant ID to verify
        raise_404: If True, raises HTTPException if not found

    Returns:
        The soft-deleted record, or None if not found

    Raises:
        HTTPException(404) if raise_404=True and record not found
        ValueError if model doesn't support soft delete

    Example:
        emission = soft_delete_tenant_record(db, Emission, emission_id, current_user.tenant_id)
        db.commit()
    """
    if not _has_soft_delete(model):
        raise ValueError(f"{model.__name__} does not support soft delete (missing deleted_at column)")

    record = get_tenant_record(db, model, record_id, tenant_id, raise_404)

    if record is None:
        return None

    record.deleted_at = datetime.utcnow()
    return record


def restore_tenant_record(
    db: Session,
    model: Any,
    record_id: Any,
    tenant_id: str,
    raise_404: bool = True
) -> Optional[Any]:
    """
    Restore a soft-deleted record by clearing deleted_at.

    Args:
        db: Database session
        model: The model class (must have deleted_at column)
        record_id: Primary key value
        tenant_id: The tenant ID to verify
        raise_404: If True, raises HTTPException if not found

    Returns:
        The restored record, or None if not found

    Raises:
        HTTPException(404) if raise_404=True and record not found
        ValueError if model doesn't support soft delete

    Example:
        emission = restore_tenant_record(db, Emission, emission_id, current_user.tenant_id)
        db.commit()
    """
    if not _has_soft_delete(model):
        raise ValueError(f"{model.__name__} does not support soft delete (missing deleted_at column)")

    # Use include_deleted=True to find soft-deleted records
    record = get_tenant_record(db, model, record_id, tenant_id, raise_404, include_deleted=True)

    if record is None:
        return None

    if record.deleted_at is None:
        # Record is not deleted, nothing to restore
        return record

    record.deleted_at = None
    return record


def verify_tenant_access(
    db: Session,
    model: Any,
    record_id: Any,
    tenant_id: str
) -> bool:
    """
    Verify that a record exists and belongs to the tenant.

    Useful for validating foreign key references before creating records.

    Args:
        db: Database session
        model: The model class
        record_id: Primary key value
        tenant_id: The tenant ID to verify

    Returns:
        True if record exists and belongs to tenant, False otherwise

    Example:
        if not verify_tenant_access(db, Emission, emission_id, current_user.tenant_id):
            raise HTTPException(404, "Parent emission not found")
    """
    return db.query(model).filter(
        model.id == record_id,
        model.tenant_id == tenant_id
    ).first() is not None


class TenantContext:
    """
    Context manager for tenant-scoped operations.

    Provides a convenient way to work with tenant-scoped data.

    Example:
        with TenantContext(db, current_user.tenant_id) as ctx:
            emissions = ctx.query(Emission).all()
            new_emission = ctx.create(Emission, scope=1, amount=100.0)
    """

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def query(self, model: Any) -> Query:
        """Get a tenant-scoped query."""
        return tenant_query(self.db, model, self.tenant_id)

    def get(self, model: Any, record_id: Any, raise_404: bool = True) -> Optional[Any]:
        """Get a single record."""
        return get_tenant_record(self.db, model, record_id, self.tenant_id, raise_404)

    def create(self, model: Any, **kwargs) -> Any:
        """Create a new record."""
        return create_tenant_record(self.db, model, self.tenant_id, **kwargs)

    def update(self, model: Any, record_id: Any, update_data: dict) -> Optional[Any]:
        """Update a record."""
        return update_tenant_record(self.db, model, record_id, self.tenant_id, update_data)

    def delete(self, model: Any, record_id: Any) -> bool:
        """Delete a record."""
        return delete_tenant_record(self.db, model, record_id, self.tenant_id)
