"""
Service layer aggregation
Provides unified access to all services
"""
from .services.ghg_calculation_service import GHGCalculationService as CalculationService
from .services.validation_service import ValidationService

__all__ = ['CalculationService', 'ValidationService']