"""
Composite repository that checks multiple sources
"""

import asyncio
from typing import Dict, List, Optional
from uuid import UUID
import logging

from app.repositories.base import EmissionFactorRepository
from app.repositories.providers.base import ExternalEmissionFactorProvider
from app.models.ghg_protocol_models import Scope3Category, EmissionFactor
from app.core.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


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
