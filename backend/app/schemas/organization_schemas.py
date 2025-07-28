"""
Organization schemas for GHG Protocol Scope 3 Calculator
"""

from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID

from app.schemas.base_schemas import BaseResponse


class OrganizationResponse(BaseResponse):
    """Organization details"""
    id: UUID
    name: str
    industry: str
    reporting_year: int
    baseline_year: Optional[int] = None
    target_year: Optional[int] = None
    sbti_committed: bool
    locations: List[str]
    created_at: datetime
    
    @classmethod
    def from_domain(cls, org: Any) -> "OrganizationResponse":
        return cls(
            id=org.id,
            name=org.name,
            industry=org.industry,
            reporting_year=org.reporting_year,
            baseline_year=org.baseline_year,
            target_year=org.target_year,
            sbti_committed=org.sbti_committed,
            locations=org.locations,
            created_at=org.created_at
        )
