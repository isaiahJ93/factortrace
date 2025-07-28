"""
Repository for calculation results
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ghg_protocol_models import (
    CategoryCalculationResult, Scope3Category, MethodologyType,
    EmissionResult, CalculationParameters
)
from app.models.ghg_database_models import CalculationResultDB


class CalculationResultRepository:
    """Repository for calculation results"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def save_result(
        self,
        result: CategoryCalculationResult
    ) -> CategoryCalculationResult:
        """Save calculation result with full audit trail"""
        db_model = CalculationResultDB(
            id=result.id,
            organization_id=result.organization_id,
            category=result.category.value,
            calculation_date=result.calculation_date,
            reporting_period=result.reporting_period,
            methodology=result.methodology.value,
            emissions_value=float(result.emissions.value),
            emissions_lower=float(result.emissions.uncertainty_lower) 
                if result.emissions.uncertainty_lower else None,
            emissions_upper=float(result.emissions.uncertainty_upper)
                if result.emissions.uncertainty_upper else None,
            activity_data_count=result.activity_data_count,
            data_quality_score=result.data_quality_score,
            emissions_by_source={k: v.dict() for k, v in (result.emissions_by_source or {}).items()},
            emissions_by_region={k: v.dict() for k, v in (result.emissions_by_region or {}).items()},
            calculation_parameters=result.calculation_parameters.dict(),
            emission_factors_used=[str(ef) for ef in result.emission_factors_used],
            activity_data_used=[str(ad) for ad in result.activity_data_used],
            assumptions=result.assumptions,
            exclusions=result.exclusions,
            validated=result.validated,
            validation_errors=result.validation_errors,
            reviewer=result.reviewer,
            review_date=result.review_date
        )
        
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        
        return result
        
    async def get_latest_result(
        self,
        organization_id: UUID,
        category: Scope3Category,
        reporting_period: Optional[date] = None
    ) -> Optional[CategoryCalculationResult]:
        """Get most recent calculation result"""
        query = select(CalculationResultDB).where(
            and_(
                CalculationResultDB.organization_id == organization_id,
                CalculationResultDB.category == category.value
            )
        )
        
        if reporting_period:
            query = query.where(CalculationResultDB.reporting_period == reporting_period)
            
        query = query.order_by(CalculationResultDB.calculation_date.desc()).limit(1)
        
        result = await self.session.execute(query)
        db_model = result.scalar_one_or_none()
        
        if db_model:
            return self._db_to_domain(db_model)
            
        return None
    
    async def get_results(
        self,
        organization_id: UUID,
        category: Optional[Scope3Category] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CategoryCalculationResult]:
        """Get calculation results with filters"""
        query = select(CalculationResultDB).where(
            CalculationResultDB.organization_id == organization_id
        )
        
        if category:
            query = query.where(CalculationResultDB.category == category.value)
        
        if start_date:
            query = query.where(CalculationResultDB.reporting_period >= start_date)
        
        if end_date:
            query = query.where(CalculationResultDB.reporting_period <= end_date)
        
        query = query.order_by(CalculationResultDB.calculation_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        db_models = result.scalars().all()
        
        return [self._db_to_domain(db) for db in db_models]
    
    async def get_result(self, calculation_id: UUID) -> Optional[CategoryCalculationResult]:
        """Get specific calculation result"""
        query = select(CalculationResultDB).where(
            CalculationResultDB.id == calculation_id
        )
        
        result = await self.session.execute(query)
        db_model = result.scalar_one_or_none()
        
        if db_model:
            return self._db_to_domain(db_model)
        
        return None
        
    def _db_to_domain(self, db: CalculationResultDB) -> CategoryCalculationResult:
        """Convert DB model to domain model"""
        return CategoryCalculationResult(
            id=db.id,
            organization_id=db.organization_id,
            category=Scope3Category(db.category),
            calculation_date=db.calculation_date,
            reporting_period=db.reporting_period,
            methodology=MethodologyType(db.methodology),
            emissions=EmissionResult(
                value=Decimal(str(db.emissions_value)),
                uncertainty_lower=Decimal(str(db.emissions_lower)) if db.emissions_lower else None,
                uncertainty_upper=Decimal(str(db.emissions_upper)) if db.emissions_upper else None
            ),
            activity_data_count=db.activity_data_count,
            data_quality_score=db.data_quality_score,
            emissions_by_source={k: EmissionResult(**v) for k, v in (db.emissions_by_source or {}).items()},
            emissions_by_region={k: EmissionResult(**v) for k, v in (db.emissions_by_region or {}).items()},
            calculation_parameters=CalculationParameters(**db.calculation_parameters),
            emission_factors_used=[UUID(ef) for ef in db.emission_factors_used],
            activity_data_used=[UUID(ad) for ad in db.activity_data_used],
            assumptions=db.assumptions,
            exclusions=db.exclusions,
            validated=db.validated,
            validation_errors=db.validation_errors,
            reviewer=db.reviewer,
            review_date=db.review_date
        )
