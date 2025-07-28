"""
Repository Layer for GHG Protocol Scope 3 Calculator
Implements data access patterns with multiple emission factor sources
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID
import asyncio
import aiohttp
import asyncpg
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import selectinload
import redis.asyncio as redis
import json
import logging

from .domain_models import (
    EmissionFactor, EmissionFactorSource, Scope3Category,
    ActivityData, Organization, CategoryCalculationResult,
    AuditLogEntry, DataQualityIndicator, TransportMode,
    WasteTreatment
)
from .database_models import (
    EmissionFactorDB, ActivityDataDB, OrganizationDB,
    CalculationResultDB, AuditLogDB
)

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis caching for emission factors"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        
    async def connect(self):
        """Initialize Redis connection"""
        self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            
    async def get(self, key: str) -> Optional[Dict]:
        """Get cached value"""
        if not self._redis:
            return None
            
        try:
            value = await self._redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
            
    async def set(self, key: str, value: Dict, ttl: int = 3600):
        """Set cached value with TTL"""
        if not self._redis:
            return
            
        try:
            await self._redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        if not self._redis:
            return
            
        try:
            async for key in self._redis.scan_iter(match=pattern):
                await self._redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")


class EmissionFactorRepository(ABC):
    """Abstract repository for emission factors"""
    
    @abstractmethod
    async def get_factor(
        self,
        category: Scope3Category,
        region: Optional[str] = None,
        year: Optional[int] = None,
        activity_type: Optional[str] = None
    ) -> Optional[EmissionFactor]:
        """Get single most appropriate emission factor"""
        pass
        
    @abstractmethod
    async def get_factors(
        self,
        category: Scope3Category,
        filters: Optional[Dict[str, any]] = None
    ) -> List[EmissionFactor]:
        """Get multiple emission factors matching criteria"""
        pass
        
    @abstractmethod
    async def save_factor(self, factor: EmissionFactor) -> EmissionFactor:
        """Save custom emission factor"""
        pass


class DatabaseEmissionFactorRepository(EmissionFactorRepository):
    """PostgreSQL implementation of emission factor repository"""
    
    def __init__(self, session: AsyncSession, cache: Optional[CacheManager] = None):
        self.session = session
        self.cache = cache
        
    async def get_factor(
        self,
        category: Scope3Category,
        region: Optional[str] = None,
        year: Optional[int] = None,
        activity_type: Optional[str] = None
    ) -> Optional[EmissionFactor]:
        """Get best matching emission factor with fallback hierarchy"""
        
        # Check cache first
        cache_key = f"ef:{category.value}:{region}:{year}:{activity_type}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return EmissionFactor(**cached)
        
        # Build query with priority ordering
        query = select(EmissionFactorDB).where(
            EmissionFactorDB.category == category.value
        )
        
        # Apply filters with fallback logic
        if region:
            query = query.where(
                or_(
                    EmissionFactorDB.region == region,
                    EmissionFactorDB.region.is_(None)
                )
            ).order_by(
                # Prioritize region-specific
                EmissionFactorDB.region.isnot(None).desc()
            )
            
        if year:
            query = query.where(
                EmissionFactorDB.year <= year
            ).order_by(
                # Most recent year
                EmissionFactorDB.year.desc()
            )
            
        if activity_type:
            query = query.where(
                or_(
                    EmissionFactorDB.metadata['activity_type'].astext == activity_type,
                    EmissionFactorDB.metadata['activity_type'].is_(None)
                )
            )
            
        # Order by data quality and source priority
        source_priority = {
            EmissionFactorSource.SUPPLIER_SPECIFIC: 1,
            EmissionFactorSource.EPA: 2,
            EmissionFactorSource.DEFRA: 3,
            EmissionFactorSource.ECOINVENT: 4,
            EmissionFactorSource.IPCC: 5,
            EmissionFactorSource.IEA: 6,
            EmissionFactorSource.CUSTOM: 7
        }
        
        query = query.order_by(
            func.coalesce(
                EmissionFactorDB.metadata['quality_score'].cast(Float),
                5.0
            ).asc()
        ).limit(1)
        
        result = await self.session.execute(query)
        factor_db = result.scalar_one_or_none()
        
        if factor_db:
            factor = self._db_to_domain(factor_db)
            
            # Cache the result
            if self.cache:
                await self.cache.set(cache_key, factor.dict(), ttl=7200)
                
            return factor
            
        return None
        
    async def get_factors(
        self,
        category: Scope3Category,
        filters: Optional[Dict[str, any]] = None
    ) -> List[EmissionFactor]:
        """Get all factors matching criteria"""
        query = select(EmissionFactorDB).where(
            EmissionFactorDB.category == category.value
        )
        
        if filters:
            if 'source' in filters:
                query = query.where(EmissionFactorDB.source == filters['source'])
            if 'region' in filters:
                query = query.where(EmissionFactorDB.region == filters['region'])
            if 'year_min' in filters:
                query = query.where(EmissionFactorDB.year >= filters['year_min'])
            if 'year_max' in filters:
                query = query.where(EmissionFactorDB.year <= filters['year_max'])
                
        result = await self.session.execute(query.order_by(EmissionFactorDB.year.desc()))
        factors_db = result.scalars().all()
        
        return [self._db_to_domain(f) for f in factors_db]
        
    async def save_factor(self, factor: EmissionFactor) -> EmissionFactor:
        """Save custom emission factor"""
        factor_db = self._domain_to_db(factor)
        self.session.add(factor_db)
        await self.session.commit()
        await self.session.refresh(factor_db)
        
        # Invalidate related cache
        if self.cache:
            await self.cache.invalidate_pattern(f"ef:{factor.category.value}:*")
            
        return self._db_to_domain(factor_db)
        
    def _db_to_domain(self, db_model: EmissionFactorDB) -> EmissionFactor:
        """Convert database model to domain model"""
        return EmissionFactor(
            id=db_model.id,
            name=db_model.name,
            category=Scope3Category(db_model.category),
            value=Decimal(str(db_model.value)),
            unit=db_model.unit,
            source=EmissionFactorSource(db_model.source),
            source_reference=db_model.source_reference,
            region=db_model.region,
            year=db_model.year,
            uncertainty_range=db_model.uncertainty_range,
            quality_indicator=DataQualityIndicator(**db_model.quality_indicator) 
                if db_model.quality_indicator else None,
            metadata=db_model.metadata or {},
            created_at=db_model.created_at,
            updated_at=db_model.updated_at
        )
        
    def _domain_to_db(self, domain_model: EmissionFactor) -> EmissionFactorDB:
        """Convert domain model to database model"""
        return EmissionFactorDB(
            id=domain_model.id,
            name=domain_model.name,
            category=domain_model.category.value,
            value=float(domain_model.value),
            unit=domain_model.unit,
            source=domain_model.source.value,
            source_reference=domain_model.source_reference,
            region=domain_model.region,
            year=domain_model.year,
            uncertainty_range=domain_model.uncertainty_range,
            quality_indicator=domain_model.quality_indicator.dict() 
                if domain_model.quality_indicator else None,
            metadata=domain_model.metadata,
            created_at=domain_model.created_at,
            updated_at=domain_model.updated_at
        )


class ExternalEmissionFactorProvider(ABC):
    """Abstract provider for external emission factor APIs"""
    
    @abstractmethod
    async def fetch_factors(
        self,
        category: Scope3Category,
        **kwargs
    ) -> List[EmissionFactor]:
        """Fetch factors from external source"""
        pass


class EPAEmissionFactorProvider(ExternalEmissionFactorProvider):
    """Provider for EPA emission factors"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.epa.gov/ghg/v1"
        
    async def fetch_factors(
        self,
        category: Scope3Category,
        material_type: Optional[str] = None,
        year: Optional[int] = None
    ) -> List[EmissionFactor]:
        """Fetch from EPA Supply Chain GHG Emission Factors"""
        
        # Map category to EPA endpoint
        endpoint_map = {
            Scope3Category.PURCHASED_GOODS_AND_SERVICES: "/supply-chain",
            Scope3Category.CAPITAL_GOODS: "/capital-goods",
            Scope3Category.FUEL_AND_ENERGY_RELATED: "/fuel-energy",
            Scope3Category.UPSTREAM_TRANSPORTATION: "/transport",
            Scope3Category.WASTE_GENERATED: "/waste"
        }
        
        endpoint = endpoint_map.get(category)
        if not endpoint:
            return []
            
        params = {
            "year": year or datetime.now().year,
            "format": "json"
        }
        
        if material_type:
            params["material"] = material_type
            
        async with aiohttp.ClientSession() as session:
            headers = {"X-API-Key": self.api_key} if self.api_key else {}
            
            try:
                async with session.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_epa_response(data, category)
                    else:
                        logger.error(f"EPA API error: {response.status}")
                        return []
            except Exception as e:
                logger.error(f"EPA API fetch error: {e}")
                return []
                
    def _parse_epa_response(
        self,
        data: Dict,
        category: Scope3Category
    ) -> List[EmissionFactor]:
        """Parse EPA API response to domain models"""
        factors = []
        
        for item in data.get("factors", []):
            factor = EmissionFactor(
                name=item["description"],
                category=category,
                value=Decimal(str(item["emission_factor"])),
                unit=item["unit"],
                source=EmissionFactorSource.EPA,
                source_reference=item.get("reference", "EPA Database"),
                region="US",  # EPA factors are US-specific
                year=item.get("year", datetime.now().year),
                uncertainty_range=(
                    item.get("uncertainty_low", 0.9),
                    item.get("uncertainty_high", 1.1)
                ),
                metadata={
                    "naics_code": item.get("naics_code"),
                    "process": item.get("process"),
                    "material": item.get("material")
                }
            )
            factors.append(factor)
            
        return factors


class DEFRAEmissionFactorProvider(ExternalEmissionFactorProvider):
    """Provider for UK DEFRA/BEIS emission factors"""
    
    def __init__(self):
        self.base_url = "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024"
        
    async def fetch_factors(
        self,
        category: Scope3Category,
        **kwargs
    ) -> List[EmissionFactor]:
        """Fetch from DEFRA conversion factors"""
        # Implementation would parse DEFRA Excel files
        # This is a placeholder showing the interface
        
        factors = []
        
        # Map categories to DEFRA sheets
        sheet_map = {
            Scope3Category.BUSINESS_TRAVEL: "Business travel- land",
            Scope3Category.FUEL_AND_ENERGY_RELATED: "WTT- fuels",
            Scope3Category.UPSTREAM_TRANSPORTATION: "Freighting goods",
            Scope3Category.WASTE_GENERATED: "Waste disposal"
        }
        
        sheet = sheet_map.get(category)
        if not sheet:
            return []
            
        # In real implementation, would download and parse Excel
        # For now, return sample factors
        if category == Scope3Category.BUSINESS_TRAVEL:
            factors.append(
                EmissionFactor(
                    name="Average car - petrol",
                    category=category,
                    value=Decimal("0.16844"),
                    unit="kgCO2e/km",
                    source=EmissionFactorSource.DEFRA,
                    source_reference="DEFRA 2024",
                    region="UK",
                    year=2024,
                    metadata={"mode": TransportMode.ROAD.value, "fuel": "petrol"}
                )
            )
            
        return factors


class CompositeEmissionFactorRepository(EmissionFactorRepository):
    """Composite repository that checks multiple sources"""
    
    def __init__(
        self,
        primary_repo: EmissionFactorRepository,
        providers: List[ExternalEmissionFactorProvider],
        cache: Optional[CacheManager] = None
    ):
        self.primary_repo = primary_repo
        self.providers = providers
        self.cache = cache
        
    async def get_factor(
        self,
        category: Scope3Category,
        region: Optional[str] = None,
        year: Optional[int] = None,
        activity_type: Optional[str] = None
    ) -> Optional[EmissionFactor]:
        """Get factor from primary repo, fallback to external providers"""
        
        # Try primary repository first
        factor = await self.primary_repo.get_factor(
            category, region, year, activity_type
        )
        
        if factor:
            return factor
            
        # Try external providers
        for provider in self.providers:
            try:
                factors = await provider.fetch_factors(
                    category,
                    year=year
                )
                
                # Filter and sort by relevance
                if factors:
                    # Simple relevance scoring
                    for f in factors:
                        score = 0
                        if f.region == region:
                            score += 10
                        if f.year == year:
                            score += 5
                        if activity_type and f.metadata.get("activity_type") == activity_type:
                            score += 8
                        f._relevance_score = score
                        
                    # Return most relevant
                    factors.sort(key=lambda x: x._relevance_score, reverse=True)
                    best_factor = factors[0]
                    
                    # Cache it
                    if self.cache:
                        cache_key = f"ef:{category.value}:{region}:{year}:{activity_type}"
                        await self.cache.set(cache_key, best_factor.dict(), ttl=3600)
                        
                    return best_factor
                    
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} error: {e}")
                continue
                
        return None
        
    async def get_factors(
        self,
        category: Scope3Category,
        filters: Optional[Dict[str, any]] = None
    ) -> List[EmissionFactor]:
        """Get factors from all sources"""
        all_factors = []
        
        # Get from primary repository
        primary_factors = await self.primary_repo.get_factors(category, filters)
        all_factors.extend(primary_factors)
        
        # Get from external providers
        tasks = []
        for provider in self.providers:
            tasks.append(provider.fetch_factors(category, **(filters or {})))
            
        provider_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in provider_results:
            if isinstance(result, list):
                all_factors.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Provider error: {result}")
                
        # Deduplicate by name and source
        seen = set()
        unique_factors = []
        for factor in all_factors:
            key = (factor.name, factor.source, factor.year)
            if key not in seen:
                seen.add(key)
                unique_factors.append(factor)
                
        return unique_factors
        
    async def save_factor(self, factor: EmissionFactor) -> EmissionFactor:
        """Save to primary repository"""
        return await self.primary_repo.save_factor(factor)


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
        
        # Convert to domain models (simplified - would need proper type mapping)
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