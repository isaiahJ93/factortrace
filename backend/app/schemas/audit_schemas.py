"""
Audit and validation schemas for GHG Protocol Scope 3 Calculator
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import Field

from app.models.ghg_protocol_models import Scope3Category
from app.schemas.base_schemas import BaseRequest, BaseResponse


class AuditLogResponse(BaseResponse):
    """Audit log entry"""
    id: UUID
    timestamp: datetime
    user: str
    action: str
    category: Optional[Scope3Category] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    changes: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class AuditTrailRequest(BaseRequest):
    """Request for audit trail"""
    entity_type: Optional[str] = Field(None, pattern="^(calculation|activity_data|emission_factor)$")
    entity_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)


class ValidationRuleSet(BaseResponse):
    """Validation rules for a category"""
    category: Scope3Category
    required_fields: List[str]
    field_constraints: Dict[str, Dict[str, Any]]
    business_rules: List[Dict[str, Any]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "business_travel",
                "required_fields": ["origin", "destination", "mode", "distance"],
                "field_constraints": {
                    "distance": {"min": 0, "max": 50000},
                    "travelers": {"min": 1, "max": 1000}
                },
                "business_rules": [
                    {
                        "rule": "air_travel_requires_cabin_class",
                        "condition": "mode == 'air'",
                        "requirement": "cabin_class is not null"
                    }
                ]
            }
        }
