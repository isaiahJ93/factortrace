"""
Validation Service for GHG Protocol Scope 3 Calculator
Validates emission factors and activity data
"""

from datetime import datetime, date
from typing import Dict, List

from app.models.ghg_protocol_models import (
    Scope3Category, EmissionFactor, ActivityData
)

import logging

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for data validation"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        
    async def validate_emission_factor(
        self,
        factor: EmissionFactor
    ) -> List[Dict[str, str]]:
        """Validate emission factor"""
        errors = []
        
        # Value must be positive
        if factor.value <= 0:
            errors.append({
                "field": "value",
                "message": "Emission factor value must be positive"
            })
            
        # Year must be reasonable
        current_year = datetime.now().year
        if factor.year > current_year:
            errors.append({
                "field": "year",
                "message": f"Year cannot be in the future (max: {current_year})"
            })
        elif factor.year < 1990:
            errors.append({
                "field": "year",
                "message": "Year must be 1990 or later"
            })
            
        # Uncertainty range validation
        if factor.uncertainty_range:
            if factor.uncertainty_range[0] >= factor.uncertainty_range[1]:
                errors.append({
                    "field": "uncertainty_range",
                    "message": "Lower bound must be less than upper bound"
                })
                
        # Category-specific validation
        category_rules = self.validation_rules.get(factor.category)
        if category_rules:
            # Check required metadata
            for required_field in category_rules.get("required_metadata", []):
                if required_field not in factor.metadata:
                    errors.append({
                        "field": "metadata",
                        "message": f"Missing required field: {required_field}"
                    })
                    
        return errors
        
    async def validate_activity_data(
        self,
        activity: ActivityData
    ) -> List[Dict[str, str]]:
        """Validate activity data"""
        errors = []
        
        # Quantity must be positive
        if activity.quantity.value <= 0:
            errors.append({
                "field": "quantity",
                "message": "Quantity must be positive"
            })
            
        # Date validation
        if activity.time_period > date.today():
            errors.append({
                "field": "time_period",
                "message": "Activity date cannot be in the future"
            })
            
        # Category-specific validation
        if activity.category == Scope3Category.BUSINESS_TRAVEL:
            # Business travel specific rules
            if "distance" in activity.metadata and activity.metadata["distance"] > 50000:
                errors.append({
                    "field": "distance",
                    "message": "Distance seems unusually high (>50,000 km)"
                })
                
        return errors
    
    async def validate_bulk_data(
        self,
        data_list: List[ActivityData]
    ) -> Dict[int, List[Dict[str, str]]]:
        """Validate multiple activity data items"""
        validation_results = {}
        
        for idx, data in enumerate(data_list):
            errors = await self.validate_activity_data(data)
            if errors:
                validation_results[idx] = errors
                
        return validation_results
        
    def _load_validation_rules(self) -> Dict[Scope3Category, Dict]:
        """Load category-specific validation rules"""
        return {
            Scope3Category.PURCHASED_GOODS_AND_SERVICES: {
                "required_metadata": ["supplier_country"],
                "quantity_limits": {"min": 0.001, "max": 1e9}
            },
            Scope3Category.BUSINESS_TRAVEL: {
                "required_metadata": ["mode", "origin", "destination"],
                "distance_limits": {"min": 1, "max": 50000}
            },
            Scope3Category.CAPITAL_GOODS: {
                "required_metadata": ["asset_type"],
                "quantity_limits": {"min": 1, "max": 1e6}
            },
            Scope3Category.FUEL_AND_ENERGY_RELATED: {
                "required_metadata": ["fuel_type"],
                "quantity_limits": {"min": 0.1, "max": 1e9}
            },
            Scope3Category.UPSTREAM_TRANSPORTATION: {
                "required_metadata": ["mode", "distance"],
                "distance_limits": {"min": 1, "max": 50000}
            },
            Scope3Category.WASTE_GENERATED: {
                "required_metadata": ["waste_type", "treatment_method"],
                "quantity_limits": {"min": 0.001, "max": 1e7}
            },
            Scope3Category.EMPLOYEE_COMMUTING: {
                "required_metadata": ["mode", "distance"],
                "distance_limits": {"min": 0.1, "max": 200}
            },
            Scope3Category.USE_OF_SOLD_PRODUCTS: {
                "required_metadata": ["product_type", "usage_profile"],
                "quantity_limits": {"min": 1, "max": 1e9}
            }
        }
