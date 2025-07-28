"""
EPA emission factor provider
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import aiohttp
import logging

from app.repositories.providers.base import ExternalEmissionFactorProvider
from app.models.ghg_protocol_models import (
    Scope3Category, EmissionFactor, EmissionFactorSource
)

logger = logging.getLogger(__name__)


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
