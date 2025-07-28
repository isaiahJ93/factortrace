"""
Calculation-related schemas for GHG Protocol Scope 3 Calculator
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Union, Any, Tuple
from uuid import UUID

from pydantic import BaseModel, Field, validator, constr, conint

from app.models.ghg_protocol_models import (
    Scope3Category, MethodologyType, EmissionFactorSource,
    DataQualityScore, TransportMode, WasteTreatment,
    TemporalResolution, UncertaintyDistribution,
    EmissionResult, DataQualityIndicator, Quantity,
    EmissionFactor, ActivityData, CategoryCalculationResult,
    Scope3Inventory
)
from app.schemas.base_schemas import BaseRequest, BaseResponse


class ActivityDataPoint(BaseRequest):
    """Single activity data point for calculations"""
    description: str = Field(..., min_length=1, max_length=500)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    data_source: str = Field(..., min_length=1, max_length=255)
    data_quality: Optional[DataQualityIndicator] = None
    metadata: Dict[str, Union[str, float, int]] = Field(default_factory=dict)
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v


class CalculationRequest(BaseRequest):
    """Request to calculate emissions for a category"""
    category: Scope3Category
    methodology: MethodologyType = MethodologyType.HYBRID
    activity_data: List[ActivityDataPoint] = Field(..., min_items=1)
    emission_factor_source: EmissionFactorSource = EmissionFactorSource.EPA
    reporting_period: date
    include_uncertainty: bool = True
    temporal_resolution: TemporalResolution = TemporalResolution.ANNUAL
    custom_emission_factors: Optional[List[UUID]] = None
    notes: Optional[str] = Field(None, max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "purchased_goods_and_services",
                "methodology": "hybrid",
                "activity_data": [
                    {
                        "description": "Steel procurement",
                        "quantity": 1000,
                        "unit": "kg",
                        "location": "US",
                        "data_source": "Purchasing records"
                    }
                ],
                "emission_factor_source": "epa",
                "reporting_period": "2024-01-01",
                "include_uncertainty": True
            }
        }


class CalculationResponse(BaseResponse):
    """Response for calculation submission"""
    calculation_id: UUID
    status: str = Field(..., pattern="^(processing|completed|failed)$")
    message: str
    estimated_completion_time: Optional[int] = None  # seconds


class EmissionResultResponse(BaseResponse):
    """Emission calculation result"""
    value: float
    uncertainty_lower: Optional[float] = None
    uncertainty_upper: Optional[float] = None
    unit: str = "kgCO2e"
    
    @classmethod
    def from_domain(cls, result: EmissionResult) -> "EmissionResultResponse":
        return cls(
            value=float(result.value),
            uncertainty_lower=float(result.uncertainty_lower) if result.uncertainty_lower else None,
            uncertainty_upper=float(result.uncertainty_upper) if result.uncertainty_upper else None,
            unit=result.unit
        )


class CategoryCalculationResponse(BaseResponse):
    """Detailed calculation results for a category"""
    id: UUID
    category: Scope3Category
    calculation_date: datetime
    reporting_period: date
    methodology: MethodologyType
    
    # Results
    emissions: EmissionResultResponse
    activity_data_count: int
    data_quality_score: float = Field(..., ge=1, le=5)
    
    # Breakdowns
    emissions_by_source: Optional[Dict[str, EmissionResultResponse]] = None
    emissions_by_region: Optional[Dict[str, EmissionResultResponse]] = None
    
    # Metadata
    assumptions: List[str] = Field(default_factory=list)
    exclusions: List[str] = Field(default_factory=list)
    validated: bool
    reviewer: Optional[str] = None
    
    @classmethod
    def from_domain(cls, result: CategoryCalculationResult) -> "CategoryCalculationResponse":
        return cls(
            id=result.id,
            category=result.category,
            calculation_date=result.calculation_date,
            reporting_period=result.reporting_period,
            methodology=result.methodology,
            emissions=EmissionResultResponse.from_domain(result.emissions),
            activity_data_count=result.activity_data_count,
            data_quality_score=result.data_quality_score,
            emissions_by_source={
                k: EmissionResultResponse.from_domain(v)
                for k, v in (result.emissions_by_source or {}).items()
            },
            emissions_by_region={
                k: EmissionResultResponse.from_domain(v)
                for k, v in (result.emissions_by_region or {}).items()
            },
            assumptions=result.assumptions,
            exclusions=result.exclusions,
            validated=result.validated,
            reviewer=result.reviewer
        )


class CalculationProgressMessage(BaseResponse):
    """Real-time calculation progress update"""
    calculation_id: UUID
    status: str
    progress: float = Field(..., ge=0, le=1)
    current_step: str
    message: Optional[str] = None
    estimated_remaining_time: Optional[int] = None  # seconds
