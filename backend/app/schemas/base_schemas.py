"""
Base schemas for GHG Protocol Scope 3 Calculator
Common base models and configurations
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel


class BaseRequest(BaseModel):
    """Base request model with common configuration"""
    class Config:
        use_enum_values = False
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }


class BaseResponse(BaseModel):
    """Base response model with common configuration"""
    class Config:
        use_enum_values = False
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v)
        }


class PaginatedResponse(BaseResponse):
    """Paginated response wrapper"""
    items: list[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class HealthCheckResponse(BaseResponse):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseResponse):
    """Standard error response"""
    error: str
    message: str
    request_id: str | None = None
    details: dict[str, Any] | None = None


class ValidationErrorResponse(BaseResponse):
    """Validation error details"""
    errors: list[dict[str, str]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "errors": [
                    {"field": "quantity", "message": "Must be positive"},
                    {"field": "year", "message": "Must be between 2000 and 2100"}
                ]
            }
        }
