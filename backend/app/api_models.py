"""
API Models for GHG Calculator
Maps to your existing schemas but provides the interface tests expect
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

# Import from your existing models
from .models.ghg_protocol_models import (
    EmissionScope, ActivityType, CalculationMethod,
    DataQuality, GHGProtocolCategory
)

class EmissionFactorCreate(BaseModel):
    activity_type: ActivityType
    scope: EmissionScope
    unit: str = Field(..., description="Unit of measurement (kg, L, kWh, etc)")
    factor: float = Field(..., gt=0, description="CO2e emission factor")
    source: str = Field(..., description="Data source reference")
    region: Optional[str] = Field(None, description="Geographic region")
    year: Optional[int] = Field(None, ge=2000, le=2030)
    uncertainty: Optional[float] = Field(None, ge=0, le=100)

class ActivityDataInput(BaseModel):
    activity_type: ActivityType
    quantity: float = Field(..., gt=0)
    unit: str
    start_date: date
    end_date: date
    data_quality: DataQuality = DataQuality.ESTIMATED
    location: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "activity_type": "electricity",
            "quantity": 1000,
            "unit": "kWh",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "data_quality": "primary",
            "location": "US-CA"
        }
    })

class CalculationRequest(BaseModel):
    """Main calculation request model"""
    company_id: UUID
    reporting_year: int = Field(..., ge=2020, le=2030)
    activity_data: List[ActivityDataInput]
    calculation_method: CalculationMethod = CalculationMethod.ACTIVITY_BASED
    include_uncertainty: bool = False
    include_benchmarks: bool = False

class EmissionResult(BaseModel):
    """Individual emission calculation result"""
    id: UUID
    activity_type: ActivityType
    scope: EmissionScope
    emissions_co2e: Decimal
    emissions_by_gas: Dict[str, Decimal] = Field(default_factory=dict)
    unit: str = "tCO2e"
    data_quality_score: float
    uncertainty_range: Optional[Dict[str, float]] = None
    calculation_methodology: str
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: lambda v: float(v)}
    )

class CalculationResponse(BaseModel):
    """Complete calculation response"""
    calculation_id: UUID
    company_id: UUID
    reporting_year: int
    total_emissions: Decimal
    scope1_emissions: Decimal
    scope2_emissions: Decimal  
    scope3_emissions: Decimal
    emissions_by_category: Dict[str, Decimal]
    emissions_by_scope: Dict[str, Decimal]
    emissions_by_gas: Dict[str, Decimal]
    data_quality_score: float
    calculation_timestamp: datetime
    detailed_results: List[EmissionResult]
    methodology_notes: List[str]
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: lambda v: float(v)}
    )

# ===== backend/src/app/repositories/__init__.py =====
"""
Repository layer for data access
Maps to your existing database operations
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import date

from ..models import ghg_database_models as models
from ..api_models import EmissionFactorCreate, ActivityDataInput

class EmissionFactorRepository:
    """Repository for emission factor data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_activity_type(
        self, 
        activity_type: str,
        region: Optional[str] = None
    ) -> Optional[models.EmissionFactor]:
        query = select(models.EmissionFactor).where(
            models.EmissionFactor.activity_type == activity_type
        )
        if region:
            query = query.where(models.EmissionFactor.region == region)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, data: EmissionFactorCreate) -> models.EmissionFactor:
        factor = models.EmissionFactor(**data.model_dump())
        self.session.add(factor)
        await self.session.commit()
        await self.session.refresh(factor)
        return factor
    
    async def get_all_for_calculation(
        self,
        activity_types: List[str],
        year: Optional[int] = None
    ) -> Dict[str, models.EmissionFactor]:
        query = select(models.EmissionFactor).where(
            models.EmissionFactor.activity_type.in_(activity_types)
        )
        if year:
            query = query.where(models.EmissionFactor.year == year)
        
        result = await self.session.execute(query)
        factors = result.scalars().all()
        
        return {f.activity_type: f for f in factors}

class ActivityDataRepository:
    """Repository for activity data operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_batch(
        self, 
        company_id: UUID,
        activity_data: List[ActivityDataInput]
    ) -> List[models.ActivityData]:
        activities = []
        for data in activity_data:
            activity = models.ActivityData(
                company_id=company_id,
                **data.model_dump()
            )
            activities.append(activity)
            self.session.add(activity)
        
        await self.session.commit()
        return activities

class CalculationResultRepository:
    """Repository for calculation results"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_calculation(
        self,
        calculation_result: Dict[str, Any]
    ) -> models.CalculationResult:
        result = models.CalculationResult(**calculation_result)
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result