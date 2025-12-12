# app/core/queries.py
"""
Query helper utilities for pagination and common query patterns.

These utilities work with the tenant isolation helpers and provide
consistent pagination across all list endpoints.
"""
from typing import TypeVar, Generic, List, Any, Tuple, Optional
from sqlalchemy.orm import Session, Query
from sqlalchemy import func

from app.schemas.common import PaginationMeta, create_pagination_meta


T = TypeVar('T')


def paginate_query(
    query: Query,
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> Tuple[List[Any], PaginationMeta]:
    """
    Apply pagination to a SQLAlchemy query.

    Args:
        query: SQLAlchemy query object (already filtered/sorted)
        page: Page number (1-indexed, default 1)
        per_page: Items per page (default 20)
        max_per_page: Maximum allowed items per page (default 100)

    Returns:
        Tuple of (items list, pagination metadata)

    Example:
        query = tenant_query(db, Emission, tenant_id).filter(Emission.scope == 3)
        items, meta = paginate_query(query, page=2, per_page=50)
    """
    # Validate and constrain parameters
    page = max(1, page)
    per_page = max(1, min(per_page, max_per_page))

    # Get total count
    total = query.count()

    # Calculate offset
    offset = (page - 1) * per_page

    # Get items for current page
    items = query.offset(offset).limit(per_page).all()

    # Create metadata
    meta = create_pagination_meta(total=total, page=page, per_page=per_page)

    return items, meta


def convert_skip_limit_to_page(skip: int, limit: int) -> Tuple[int, int]:
    """
    Convert skip/limit pagination to page/per_page.

    Useful for backwards compatibility with existing endpoints.

    Args:
        skip: Number of items to skip
        limit: Maximum items to return

    Returns:
        Tuple of (page, per_page)
    """
    per_page = limit
    page = (skip // limit) + 1 if limit > 0 else 1
    return page, per_page


def apply_sorting(
    query: Query,
    sort_by: Optional[str],
    sort_order: str = "desc",
    allowed_fields: Optional[List[str]] = None,
    model: Any = None
) -> Query:
    """
    Apply sorting to a query with validation.

    Args:
        query: SQLAlchemy query
        sort_by: Field name to sort by
        sort_order: "asc" or "desc"
        allowed_fields: List of field names allowed for sorting (security)
        model: SQLAlchemy model class

    Returns:
        Query with sorting applied

    Example:
        query = apply_sorting(
            query,
            sort_by="created_at",
            sort_order="desc",
            allowed_fields=["created_at", "amount"],
            model=Emission
        )
    """
    if not sort_by:
        return query

    # Validate field name (security - prevent SQL injection)
    if allowed_fields and sort_by not in allowed_fields:
        return query

    # Get the column from the model
    if model and hasattr(model, sort_by):
        column = getattr(model, sort_by)

        if sort_order.lower() == "asc":
            query = query.order_by(column.asc())
        else:
            query = query.order_by(column.desc())

    return query


class PaginatedQuery(Generic[T]):
    """
    Helper class for building paginated queries with fluent interface.

    Example:
        result = (
            PaginatedQuery(db, Emission, tenant_id)
            .filter(Emission.scope == 3)
            .sort_by("created_at", "desc")
            .paginate(page=1, per_page=20)
        )
        items = result.items
        meta = result.meta
    """

    def __init__(
        self,
        db: Session,
        model: Any,
        tenant_id: str,
        include_deleted: bool = False
    ):
        from app.core.tenant import tenant_query
        self._query = tenant_query(db, model, tenant_id, include_deleted)
        self._model = model

    def filter(self, *args) -> 'PaginatedQuery[T]':
        """Add filter conditions."""
        self._query = self._query.filter(*args)
        return self

    def sort_by(
        self,
        field: str,
        order: str = "desc",
        allowed_fields: Optional[List[str]] = None
    ) -> 'PaginatedQuery[T]':
        """Add sorting."""
        self._query = apply_sorting(
            self._query,
            sort_by=field,
            sort_order=order,
            allowed_fields=allowed_fields,
            model=self._model
        )
        return self

    def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100
    ) -> Tuple[List[T], PaginationMeta]:
        """Execute query with pagination."""
        return paginate_query(
            self._query,
            page=page,
            per_page=per_page,
            max_per_page=max_per_page
        )

    @property
    def query(self) -> Query:
        """Get the underlying query for advanced operations."""
        return self._query
