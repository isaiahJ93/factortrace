"""
Repository for activity data management
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ghg_protocol_models import (
    ActivityData, Scope3Category, Quantity, DataQualityIndicator
)
from app.models.ghg_database_models import ActivityDataDB


class ActivityDataRepository:
    """Repository for activity data management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def save_activity_data(
        self,
        activity_data: ActivityData,
        organization_id: UUID
    ) -> ActivityData:
        """Save activity data"""
        db_model = ActivityDataDB(
            id=activity_data.id,
            organization_id=organization_id,
            category=activity_data.category.value,
            description=activity_data.description,
            quantity_value=float(activity_data.quantity.value),
            quantity_unit=activity_data.quantity.unit,
            location=activity_data.location,
            time_period=activity_data.time_period,
            data_source=activity_data.data_source,
            quality_indicator=activity_data.quality_indicator.dict(),
            metadata=activity_data.metadata,
            created_at=datetime.utcnow()
        )
        
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        
        return activity_data
        
    async def get_activity_data(
        self,
        organization_id: UUID,
        category: Optional[Scope3Category] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ActivityData]:
        """Get activity data with filters"""
        query = select(ActivityDataDB).where(
            ActivityDataDB.organization_id == organization_id
        )
        
        if category:
            query = query.where(ActivityDataDB.category == category.value)
            
        if start_date:
            query = query.where(ActivityDataDB.time_period >= start_date)
            
        if end_date:
            query = query.where(ActivityDataDB.time_period <= end_date)
            
        result = await self.session.execute(
            query.order_by(ActivityDataDB.time_period.desc())
        )
        
        db_models = result.scalars().all()
        
        # Convert to domain models
        return [
            ActivityData(
                id=db.id,
                category=Scope3Category(db.category),
                description=db.description,
                quantity=Quantity(value=Decimal(str(db.quantity_value)), unit=db.quantity_unit),
                location=db.location,
                time_period=db.time_period,
                data_source=db.data_source,
                quality_indicator=DataQualityIndicator(**db.quality_indicator),
                metadata=db.metadata or {}
            )
            for db in db_models
        ]
        
    async def bulk_save(
        self,
        activity_data_list: List[ActivityData],
        organization_id: UUID
    ) -> List[ActivityData]:
        """Bulk save activity data"""
        db_models = [
            ActivityDataDB(
                id=ad.id,
                organization_id=organization_id,
                category=ad.category.value,
                description=ad.description,
                quantity_value=float(ad.quantity.value),
                quantity_unit=ad.quantity.unit,
                location=ad.location,
                time_period=ad.time_period,
                data_source=ad.data_source,
                quality_indicator=ad.quality_indicator.dict(),
                metadata=ad.metadata,
                created_at=datetime.utcnow()
            )
            for ad in activity_data_list
        ]
        
        self.session.add_all(db_models)
        await self.session.commit()
        
        return activity_data_list
