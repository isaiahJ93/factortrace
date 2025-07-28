"""
Repository for immutable audit log
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ghg_protocol_models import AuditLogEntry, Scope3Category
from app.models.ghg_database_models import AuditLogDB


class AuditLogRepository:
    """Repository for immutable audit log"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def log_action(
        self,
        organization_id: UUID,
        user: str,
        action: str,
        category: Optional[Scope3Category] = None,
        calculation_id: Optional[UUID] = None,
        previous_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        reason: Optional[str] = None
    ) -> AuditLogEntry:
        """Create immutable audit log entry"""
        entry = AuditLogEntry(
            organization_id=organization_id,
            user=user,
            action=action,
            category=category,
            calculation_id=calculation_id,
            previous_value=previous_value,
            new_value=new_value,
            reason=reason
        )
        
        db_model = AuditLogDB(
            id=entry.id,
            timestamp=entry.timestamp,
            organization_id=entry.organization_id,
            user=entry.user,
            action=entry.action,
            category=entry.category.value if entry.category else None,
            calculation_id=entry.calculation_id,
            previous_value=entry.previous_value,
            new_value=entry.new_value,
            reason=entry.reason
        )
        
        self.session.add(db_model)
        await self.session.commit()
        
        return entry
        
    async def get_audit_trail(
        self,
        organization_id: UUID,
        calculation_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLogEntry]:
        """Get audit trail with filters"""
        query = select(AuditLogDB).where(
            AuditLogDB.organization_id == organization_id
        )
        
        if calculation_id:
            query = query.where(AuditLogDB.calculation_id == calculation_id)
            
        if start_date:
            query = query.where(AuditLogDB.timestamp >= start_date)
            
        if end_date:
            query = query.where(AuditLogDB.timestamp <= end_date)
            
        result = await self.session.execute(
            query.order_by(AuditLogDB.timestamp.desc())
        )
        
        db_models = result.scalars().all()
        
        return [
            AuditLogEntry(
                id=db.id,
                timestamp=db.timestamp,
                organization_id=db.organization_id,
                user=db.user,
                action=db.action,
                category=Scope3Category(db.category) if db.category else None,
                calculation_id=db.calculation_id,
                previous_value=db.previous_value,
                new_value=db.new_value,
                reason=db.reason
            )
            for db in db_models
        ]
