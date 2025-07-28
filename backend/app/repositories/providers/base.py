"""
Abstract provider for external emission factor APIs
"""

from abc import ABC, abstractmethod
from typing import List

from app.models.ghg_protocol_models import Scope3Category, EmissionFactor


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
