"""
UK DEFRA/BEIS emission factor provider
"""

from decimal import Decimal
from typing import List

from app.repositories.providers.base import ExternalEmissionFactorProvider
from app.models.ghg_protocol_models import (
    Scope3Category, EmissionFactor, EmissionFactorSource, TransportMode
)


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
