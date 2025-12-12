# app/schemas/common.py
"""
Common Pydantic schemas used across the API.

These schemas provide standard response wrappers for consistency.
"""
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field


# Generic type for paginated items
T = TypeVar('T')


class PaginationMeta(BaseModel):
    """Pagination metadata returned with list responses."""
    total: int = Field(..., description="Total number of items matching the query")
    page: int = Field(..., description="Current page number (1-indexed)")
    per_page: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.

    Use this for list endpoints that return paginated data.

    Example response:
    {
        "items": [...],
        "meta": {
            "total": 100,
            "page": 1,
            "per_page": 20,
            "pages": 5,
            "has_next": true,
            "has_prev": false
        }
    }
    """
    items: List[T] = Field(..., description="List of items for the current page")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class ErrorDetail(BaseModel):
    """Structured error detail."""
    loc: Optional[List[str]] = Field(None, description="Location of the error (field path)")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type code")


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = Field(..., description="Human-readable error message")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Detailed errors for validation failures")
    request_id: Optional[str] = Field(None, description="Request ID for support inquiries")


class SuccessResponse(BaseModel):
    """Standard success response for non-data operations."""
    message: str = Field(..., description="Success message")
    id: Optional[int] = Field(None, description="ID of affected resource if applicable")


def create_pagination_meta(
    total: int,
    page: int,
    per_page: int
) -> PaginationMeta:
    """
    Create pagination metadata from query parameters.

    Args:
        total: Total number of items
        page: Current page (1-indexed)
        per_page: Items per page

    Returns:
        PaginationMeta object
    """
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return PaginationMeta(
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )
