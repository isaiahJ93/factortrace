"""
PostgreSQL implementation of emission factor repository
IMPROVED VERSION - Dr. Chen-Nakamura enhancements
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Float
from app.repositories.base import EmissionFactorRepository, CacheableRepository, AuditableRepository
from app.models.ghg_protocol_models import (
    EmissionFactor, EmissionFactorSource, Scope3Category,
    DataQualityIndicator
)
from app.models.ghg_database_models import EmissionFactorDB
from app.core.cache.cache_manager import CacheManager
import logging
logger = logging.getLogger(__name__)

class DatabaseEmissionFactorRepository(EmissionFactorRepository, CacheableRepository, AuditableRepository):
    """
    PostgreSQL implementation of emission factor repository
    IMPROVED: Added caching, auditing, and better query optimization
    """
    
    def __init__(self, session: AsyncSession, cache: Optional[CacheManager] = None):
        self.session = session
        self.cache = cache
        self._query_count = 0  # IMPROVEMENT: Track queries for monitoring
        
    async def get_factor(
        self,
        category: Scope3Category,
        region: Optional[str] = None,
        year: Optional[int] = None,
        activity_type: Optional[str] = None
    ) -> Optional[EmissionFactor]:
        """
        Get best matching emission factor with fallback hierarchy
        IMPROVED: Better fallback logic and query optimization
        """
        
        # Check cache first
        cache_key = f"ef:{category.value}:{region}:{year}:{activity_type}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {cache_key}")
                return EmissionFactor(**cached)
        
        # IMPROVEMENT: Build optimized query with scoring
        query = select(
            EmissionFactorDB,
            # Calculate match score
            func.case(
                # Exact activity type match = 100 points
                (EmissionFactorDB.activity_type == activity_type, 100),
                # Null activity type (generic) = 50 points
                (EmissionFactorDB.activity_type.is_(None), 50),
                else_=0
            ).label('activity_score'),
            func.case(
                # Exact region match = 100 points
                (EmissionFactorDB.region == region, 100),
                # Global region = 50 points
                (EmissionFactorDB.region == "GLOBAL", 50),
                # Null region = 25 points
                (EmissionFactorDB.region.is_(None), 25),
                else_=0
            ).label('region_score'),
            # Year proximity score (max 100 points, -20 per year difference)
            func.greatest(
                0,
                100 - func.abs(EmissionFactorDB.year - year) * 20
            ).label('year_score') if year else 0
        ).where(
            and_(
                EmissionFactorDB.category == category.value,
                EmissionFactorDB.is_active == True,  # IMPROVEMENT: Check active status
                # IMPROVEMENT: Only use factors from last 5 years
                EmissionFactorDB.year >= (year - 5) if year else True
            )
        )
        
        # IMPROVEMENT: Order by combined score
        query = query.order_by(
            text('activity_score + region_score + year_score DESC'),
            EmissionFactorDB.data_quality_score.asc(),  # Better quality = lower score
            EmissionFactorDB.updated_at.desc()  # Most recent updates
        ).limit(1)
        
        self._query_count += 1
        result = await self.session.execute(query)
        row = result.first()
        
        if row:
            factor_db = row[0]
            factor = self._db_to_domain(factor_db)
            
            # IMPROVEMENT: Log match quality for monitoring
            total_score = row.activity_score + row.region_score + row.year_score
            logger.info(f"Found factor with match score {total_score} for {category.value}")
            
            # Cache the result
            if self.cache:
                await self.cache.set(cache_key, factor.dict(), ttl=3600)
                
            return factor
            
        logger.warning(f"No emission factor found for {category.value}")
        return None
        
    async def get_factors(
        self,
        category: Scope3Category,
        filters: Optional[Dict[str, any]] = None
    ) -> List[EmissionFactor]:
        """Get all factors matching criteria"""
        query = select(EmissionFactorDB).where(
            and_(
                EmissionFactorDB.category == category.value,
                EmissionFactorDB.is_active == True
            )
        )
        
        if filters:
            # IMPROVEMENT: More flexible filtering
            if 'source' in filters:
                query = query.where(EmissionFactorDB.source == filters['source'])
            if 'region' in filters:
                if isinstance(filters['region'], list):
                    query = query.where(EmissionFactorDB.region.in_(filters['region']))
                else:
                    query = query.where(EmissionFactorDB.region == filters['region'])
            if 'year_min' in filters:
                query = query.where(EmissionFactorDB.year >= filters['year_min'])
            if 'year_max' in filters:
                query = query.where(EmissionFactorDB.year <= filters['year_max'])
            if 'quality_min' in filters:
                query = query.where(EmissionFactorDB.data_quality_score >= filters['quality_min'])
        
        query = query.order_by(EmissionFactorDB.year.desc(), EmissionFactorDB.data_quality_score.asc())
        
        self._query_count += 1
        result = await self.session.execute(query)
        factors_db = result.scalars().all()
        
        return [self._db_to_domain(f) for f in factors_db]
        
    async def save_factor(self, factor: EmissionFactor) -> EmissionFactor:
        """Save custom emission factor"""
        factor_db = self._domain_to_db(factor)
        factor_db.created_at = datetime.utcnow()
        factor_db.updated_at = datetime.utcnow()
        
        self.session.add(factor_db)
        await self.session.commit()
        await self.session.refresh(factor_db)
        
        # Invalidate related cache
        if self.cache:
            await self.cache.invalidate_pattern(f"ef:{factor.category.value}:*")
            
        # IMPROVEMENT: Record audit trail
        await self.record_change(
            entity_id=factor_db.id,
            change_type="CREATE",
            new_value=factor.dict()
        )
            
        return self._db_to_domain(factor_db)
    
    # IMPROVEMENT: Implement new interface methods
    async def get_factor_by_id(self, factor_id: UUID) -> Optional[EmissionFactor]:
        """Get emission factor by ID"""
        cache_key = f"ef:id:{factor_id}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return EmissionFactor(**cached)
        
        result = await self.session.execute(
            select(EmissionFactorDB).where(EmissionFactorDB.id == factor_id)
        )
        factor_db = result.scalar_one_or_none()
        
        if factor_db:
            factor = self._db_to_domain(factor_db)
            if self.cache:
                await self.cache.set(cache_key, factor.dict(), ttl=3600)
            return factor
        return None
    
    async def update_factor(self, factor_id: UUID, updates: Dict[str, any]) -> Optional[EmissionFactor]:
        """Update existing emission factor"""
        factor_db = await self.session.get(EmissionFactorDB, factor_id)
        if not factor_db:
            return None
        
        old_value = self._db_to_domain(factor_db).dict()
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(factor_db, key):
                setattr(factor_db, key, value)
        
        factor_db.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(factor_db)
        
        new_factor = self._db_to_domain(factor_db)
        
        # Invalidate cache
        if self.cache:
            await self.cache.delete(f"ef:id:{factor_id}")
            await self.cache.invalidate_pattern(f"ef:{new_factor.category.value}:*")
        
        # Record audit
        await self.record_change(
            entity_id=factor_id,
            change_type="UPDATE",
            old_value=old_value,
            new_value=new_factor.dict()
        )
        
        return new_factor
    
    async def delete_factor(self, factor_id: UUID) -> bool:
        """Soft delete emission factor"""
        factor_db = await self.session.get(EmissionFactorDB, factor_id)
        if not factor_db:
            return False
        
        old_value = self._db_to_domain(factor_db).dict()
        
        # Soft delete
        factor_db.is_active = False
        factor_db.updated_at = datetime.utcnow()
        await self.session.commit()
        
        # Invalidate cache
        if self.cache:
            await self.cache.delete(f"ef:id:{factor_id}")
            await self.cache.invalidate_pattern(f"ef:{factor_db.category}:*")
        
        # Record audit
        await self.record_change(
            entity_id=factor_id,
            change_type="DELETE",
            old_value=old_value
        )
        
        return True
    
    async def get_factors_by_source(self, source: str) -> List[EmissionFactor]:
        """Get all factors from a specific source"""
        result = await self.session.execute(
            select(EmissionFactorDB).where(
                and_(
                    EmissionFactorDB.source == source,
                    EmissionFactorDB.is_active == True
                )
            ).order_by(EmissionFactorDB.category, EmissionFactorDB.year.desc())
        )
        factors_db = result.scalars().all()
        return [self._db_to_domain(f) for f in factors_db]
    
    async def get_latest_factors(self, limit: int = 10) -> List[EmissionFactor]:
        """Get most recently added/updated factors"""
        result = await self.session.execute(
            select(EmissionFactorDB).where(
                EmissionFactorDB.is_active == True
            ).order_by(EmissionFactorDB.updated_at.desc()).limit(limit)
        )
        factors_db = result.scalars().all()
        return [self._db_to_domain(f) for f in factors_db]
    
    async def search_factors(
        self,
        query: str,
        category: Optional[Scope3Category] = None,
        limit: int = 20
    ) -> List[EmissionFactor]:
        """Search factors by text query"""
        search_query = select(EmissionFactorDB).where(
            and_(
                or_(
                    EmissionFactorDB.activity_type.ilike(f"%{query}%"),
                    EmissionFactorDB.description.ilike(f"%{query}%"),
                    EmissionFactorDB.metadata.cast(String).ilike(f"%{query}%")
                ),
                EmissionFactorDB.is_active == True
            )
        )
        
        if category:
            search_query = search_query.where(EmissionFactorDB.category == category.value)
        
        search_query = search_query.order_by(
            EmissionFactorDB.data_quality_score.asc(),
            EmissionFactorDB.year.desc()
        ).limit(limit)
        
        result = await self.session.execute(search_query)
        factors_db = result.scalars().all()
        return [self._db_to_domain(f) for f in factors_db]
    
    async def get_factor_history(
        self,
        category: Scope3Category,
        activity_type: str,
        region: Optional[str] = None
    ) -> List[EmissionFactor]:
        """Get historical factors for trend analysis"""
        query = select(EmissionFactorDB).where(
            and_(
                EmissionFactorDB.category == category.value,
                EmissionFactorDB.activity_type == activity_type,
                EmissionFactorDB.is_active == True
            )
        )
        
        if region:
            query = query.where(EmissionFactorDB.region == region)
        
        query = query.order_by(EmissionFactorDB.year.asc())
        
        result = await self.session.execute(query)
        factors_db = result.scalars().all()
        return [self._db_to_domain(f) for f in factors_db]
    
    async def bulk_create_factors(self, factors: List[EmissionFactor]) -> List[EmissionFactor]:
        """Create multiple factors efficiently"""
        factor_dbs = []
        for factor in factors:
            factor_db = self._domain_to_db(factor)
            factor_db.created_at = datetime.utcnow()
            factor_db.updated_at = datetime.utcnow()
            factor_dbs.append(factor_db)
        
        self.session.add_all(factor_dbs)
        await self.session.commit()
        
        # Invalidate cache
        if self.cache:
            categories = set(f.category.value for f in factors)
            for category in categories:
                await self.cache.invalidate_pattern(f"ef:{category}:*")
        
        return factors
    
    async def bulk_update_factors(self, updates: List[Dict[str, any]]) -> int:
        """Update multiple factors efficiently"""
        updated_count = 0
        for update in updates:
            factor_id = update.pop('id')
            factor_db = await self.session.get(EmissionFactorDB, factor_id)
            if factor_db:
                for key, value in update.items():
                    if hasattr(factor_db, key):
                        setattr(factor_db, key, value)
                factor_db.updated_at = datetime.utcnow()
                updated_count += 1
        
        await self.session.commit()
        
        # Invalidate cache
        if self.cache:
            await self.cache.invalidate_pattern("ef:*")
        
        return updated_count
    
    # Cache interface implementation
    async def invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate cache entries"""
        if self.cache:
            if pattern:
                await self.cache.invalidate_pattern(pattern)
            else:
                await self.cache.invalidate_pattern("ef:*")
    
    async def preload_cache(self, categories: Optional[List[Scope3Category]] = None):
        """Preload frequently used data into cache"""
        if not self.cache:
            return
        
        # Get categories to preload
        if not categories:
            categories = list(Scope3Category)
        
        # Common regions to preload
        regions = ["GLOBAL", "US", "EU", "UK", "CN"]
        current_year = datetime.now().year
        
        for category in categories:
            for region in regions:
                # Preload current year factors
                factor = await self.get_factor(
                    category=category,
                    region=region,
                    year=current_year
                )
                if factor:
                    logger.info(f"Preloaded {category.value} - {region} - {current_year}")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics"""
        if self.cache:
            return self.cache.get_stats()
        return {"cache_enabled": False}
    
    # Audit interface implementation
    async def get_audit_trail(
        self,
        entity_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, any]]:
        """Get audit trail for an entity"""
        # This would query an audit table in a real implementation
        # For now, return placeholder
        return []
    
    async def record_change(
        self,
        entity_id: UUID,
        change_type: str,
        old_value: Optional[Dict[str, any]] = None,
        new_value: Optional[Dict[str, any]] = None,
        user_id: Optional[UUID] = None
    ):
        """Record a change in audit trail"""
        # This would insert into an audit table in a real implementation
        logger.info(f"Audit: {change_type} on EmissionFactor {entity_id}")
        
    def _db_to_domain(self, db_model: EmissionFactorDB) -> EmissionFactor:
        """Convert database model to domain model"""
        return EmissionFactor(
            factor_id=str(db_model.id),
            category=Scope3Category(db_model.category),
            value=Decimal(str(db_model.factor_value)),
            unit=db_model.unit,
            source=EmissionFactorSource(
                name=db_model.source,
                year=db_model.year,
                url=db_model.source_url
            ),
            region=db_model.region,
            activity_type=db_model.activity_type,
            data_quality=DataQualityIndicator(
                tier=db_model.data_quality_tier,
                score=db_model.data_quality_score,
                uncertainty_percent=Decimal(str(db_model.uncertainty_percent or 30))
            ),
            metadata=db_model.metadata or {}
        )
        
    def _domain_to_db(self, domain_model: EmissionFactor) -> EmissionFactorDB:
        """Convert domain model to database model"""
        return EmissionFactorDB(
            category=domain_model.category.value,
            factor_value=float(domain_model.value),
            unit=domain_model.unit,
            source=domain_model.source.name,
            year=domain_model.source.year,
            source_url=domain_model.source.url,
            region=domain_model.region,
            activity_type=domain_model.activity_type,
            data_quality_tier=domain_model.data_quality.tier,
            data_quality_score=domain_model.data_quality.score,
            uncertainty_percent=float(domain_model.data_quality.uncertainty_percent),
            metadata=domain_model.metadata,
            is_active=True  # IMPROVEMENT: Default to active
        )