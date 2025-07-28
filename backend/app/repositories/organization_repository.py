"""
Repository for organization management
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ghg_protocol_models import Organization
from app.models.ghg_database_models import OrganizationDB


class OrganizationRepository:
    """Repository for organization management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, organization_id: UUID) -> Optional[Organization]:
        """Get organization by ID"""
        query = select(OrganizationDB).where(
            OrganizationDB.id == organization_id
        )
        
        result = await self.session.execute(query)
        db_model = result.scalar_one_or_none()
        
        if db_model:
            return Organization(
                id=db_model.id,
                name=db_model.name,
                industry=db_model.industry,
                reporting_year=db_model.reporting_year,
                locations=db_model.locations or [],
                baseline_year=db_model.baseline_year,
                target_year=db_model.target_year,
                sbti_committed=db_model.sbti_committed,
                metadata=db_model.metadata or {}
            )
        
        return None
