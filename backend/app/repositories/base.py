"""
Base repository interfaces for emission factors
IMPROVED VERSION - Dr. Chen-Nakamura enhancements
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, TypeVar, Generic, Union
from uuid import UUID
from datetime import datetime

# IMPROVEMENT: Add async support
try:
    from sqlalchemy.ext.asyncio import AsyncSession
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

from sqlalchemy.orm import Session

from app.models.ghg_protocol_models import (
    Scope3Category, EmissionFactor
)

# IMPROVEMENT: Generic type for model classes
T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository with common functionality
    IMPROVEMENT: Added generic typing and common methods
    """
    
    def __init__(self, session: Union[Session, 'AsyncSession']):
        self.session = session
        self.is_async = ASYNC_AVAILABLE and hasattr(session, 'execute')
    
    # IMPROVEMENT: Common transaction methods
    async def commit(self):
        """Commit transaction (async-aware)"""
        if self.is_async:
            await self.session.commit()
        else:
            self.session.commit()
    
    async def rollback(self):
        """Rollback transaction (async-aware)"""
        if self.is_async:
            await self.session.rollback()
        else:
            self.session.rollback()
    
    async def flush(self):
        """Flush session (async-aware)"""
        if self.is_async:
            await self.session.flush()
        else:
            self.session.flush()
    
    async def refresh(self, instance: T):
        """Refresh instance (async-aware)"""
        if self.is_async:
            await self.session.refresh(instance)
        else:
            self.session.refresh(instance)

class EmissionFactorRepository(ABC):
    """
    Abstract repository for emission factors
    IMPROVEMENT: Enhanced with caching support and metadata
    """
    
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
    
    # IMPROVEMENT: Additional methods for better functionality
    @abstractmethod
    async def get_factor_by_id(self, factor_id: UUID) -> Optional[EmissionFactor]:
        """Get emission factor by ID"""
        pass
    
    @abstractmethod
    async def update_factor(self, factor_id: UUID, updates: Dict[str, any]) -> Optional[EmissionFactor]:
        """Update existing emission factor"""
        pass
    
    @abstractmethod
    async def delete_factor(self, factor_id: UUID) -> bool:
        """Delete emission factor (soft delete recommended)"""
        pass
    
    @abstractmethod
    async def get_factors_by_source(self, source: str) -> List[EmissionFactor]:
        """Get all factors from a specific source"""
        pass
    
    @abstractmethod
    async def get_latest_factors(self, limit: int = 10) -> List[EmissionFactor]:
        """Get most recently added/updated factors"""
        pass
    
    @abstractmethod
    async def search_factors(
        self,
        query: str,
        category: Optional[Scope3Category] = None,
        limit: int = 20
    ) -> List[EmissionFactor]:
        """Search factors by text query"""
        pass
    
    @abstractmethod
    async def get_factor_history(
        self,
        category: Scope3Category,
        activity_type: str,
        region: Optional[str] = None
    ) -> List[EmissionFactor]:
        """Get historical factors for trend analysis"""
        pass
    
    # IMPROVEMENT: Bulk operations
    @abstractmethod
    async def bulk_create_factors(self, factors: List[EmissionFactor]) -> List[EmissionFactor]:
        """Create multiple factors efficiently"""
        pass
    
    @abstractmethod
    async def bulk_update_factors(self, updates: List[Dict[str, any]]) -> int:
        """Update multiple factors efficiently"""
        pass

# IMPROVEMENT: Cache interface for repositories
class CacheableRepository(ABC):
    """Mixin for repositories that support caching"""
    
    @abstractmethod
    async def invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate cache entries"""
        pass
    
    @abstractmethod
    async def preload_cache(self, categories: Optional[List[Scope3Category]] = None):
        """Preload frequently used data into cache"""
        pass
    
    @abstractmethod
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics"""
        pass

# IMPROVEMENT: Audit interface for repositories
class AuditableRepository(ABC):
    """Mixin for repositories that support audit trails"""
    
    @abstractmethod
    async def get_audit_trail(
        self,
        entity_id: UUID,
        limit: int = 50
    ) -> List[Dict[str, any]]:
        """Get audit trail for an entity"""
        pass
    
    @abstractmethod
    async def record_change(
        self,
        entity_id: UUID,
        change_type: str,
        old_value: Optional[Dict[str, any]] = None,
        new_value: Optional[Dict[str, any]] = None,
        user_id: Optional[UUID] = None
    ):
        """Record a change in audit trail"""
        pass

# IMPROVEMENT: Metrics interface for repositories
class MetricsAwareRepository(ABC):
    """Mixin for repositories that track metrics"""
    
    @abstractmethod
    def increment_metric(self, metric_name: str, value: float = 1.0):
        """Increment a metric counter"""
        pass
    
    @abstractmethod
    def record_timing(self, metric_name: str, duration_ms: float):
        """Record timing metric"""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, any]:
        """Get current metrics"""
        pass