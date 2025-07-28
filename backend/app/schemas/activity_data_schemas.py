"""
Activity data schemas for GHG Protocol Scope 3 Calculator
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Any
from typing import Optional
from pydantic import Field

from app.models.ghg_protocol_models import (
    Scope3Category, DataQualityScore, ActivityData,
    Quantity, DataQualityIndicator
)
from app.schemas.base_schemas import BaseRequest


class ActivityDataUploadRequest(BaseRequest):
    """Single activity data for upload"""
    category: Scope3Category
    description: str
    quantity_value: float = Field(..., gt=0)
    quantity_unit: str
    location: Optional[str] = None
    time_period: date
    data_source: str
    quality_scores: Dict[str, DataQualityScore]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_domain(self) -> ActivityData:
        """Convert to domain model"""
        return ActivityData(
            category=self.category,
            description=self.description,
            quantity=Quantity(
                value=Decimal(str(self.quantity_value)),
                unit=self.quantity_unit
            ),
            location=self.location,
            time_period=self.time_period,
            data_source=self.data_source,
            quality_indicator=DataQualityIndicator(**self.quality_scores),
            metadata=self.metadata
        )


class BulkActivityDataRequest(BaseRequest):
    """Bulk upload of activity data"""
    activity_data: List[ActivityDataUploadRequest] = Field(..., min_items=1, max_items=10000)
    validate_only: bool = False
    replace_existing: bool = False
