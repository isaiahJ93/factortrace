"""
Emission factor schemas for GHG Protocol Scope 3 Calculator
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID

from pydantic import Field, validator, constr, conint
from typing import Optional
from app.models.ghg_protocol_models import (
    Scope3Category, EmissionFactorSource,
    DataQualityIndicator, EmissionFactor
)
from app.schemas.base_schemas import BaseRequest, BaseResponse


class EmissionFactorCreateRequest(BaseRequest):
    """Request to create custom emission factor"""
    name: constr(min_length=1, max_length=255)
    category: Scope3Category
    value: float = Field(..., gt=0)
    unit: constr(min_length=1, max_length=50)
    source_reference: constr(min_length=1)
    source_url: Optional[str] = Field(None, max_length=500)
    region: Optional[constr(max_length=100)] = None
    year: conint(ge=2000, le=2100)
    uncertainty_range: Optional[Tuple[float, float]] = Field(None)
    quality_indicator: Optional[DataQualityIndicator] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('uncertainty_range')
    def validate_uncertainty(cls, v):
        if v and (v[0] < 0 or v[1] < v[0]):
            raise ValueError("Invalid uncertainty range")
        return v
    
    def to_domain(self, organization_id: UUID) -> EmissionFactor:
        """Convert to domain model"""
        return EmissionFactor(
            name=self.name,
            category=self.category,
            value=Decimal(str(self.value)),
            unit=self.unit,
            source=EmissionFactorSource.CUSTOM,
            source_reference=self.source_reference,
            region=self.region,
            year=self.year,
            uncertainty_range=self.uncertainty_range,
            quality_indicator=self.quality_indicator,
            metadata={**self.metadata, "organization_id": str(organization_id)}
        )


class EmissionFactorResponse(BaseResponse):
    """Emission factor details"""
    id: UUID
    name: str
    category: Scope3Category
    value: float
    unit: str
    source: EmissionFactorSource
    source_reference: str
    region: Optional[str] = None
    year: int
    uncertainty_range: Optional[Tuple[float, float]] = None
    quality_score: Optional[float] = None
    created_at: datetime
    
    @classmethod
    def from_domain(cls, factor: EmissionFactor) -> "EmissionFactorResponse":
        return cls(
            id=factor.id,
            name=factor.name,
            category=factor.category,
            value=float(factor.value),
            unit=factor.unit,
            source=factor.source,
            source_reference=factor.source_reference,
            region=factor.region,
            year=factor.year,
            uncertainty_range=factor.uncertainty_range,
            quality_score=factor.quality_indicator.overall_score if factor.quality_indicator else None,
            created_at=factor.created_at
        )
