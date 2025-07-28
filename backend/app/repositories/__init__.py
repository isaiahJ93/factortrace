"""
Repository layer for GHG Protocol Scope 3 Calculator
"""

from .base import EmissionFactorRepository
from .emission_factor_repository import DatabaseEmissionFactorRepository
from .composite_repository import CompositeEmissionFactorRepository
from .activity_data_repository import ActivityDataRepository
from .calculation_result_repository import CalculationResultRepository
from .audit_log_repository import AuditLogRepository
from .organization_repository import OrganizationRepository

# Providers
from .providers.base import ExternalEmissionFactorProvider
from .providers.epa_provider import EPAEmissionFactorProvider
from .providers.defra_provider import DEFRAEmissionFactorProvider

__all__ = [
    'EmissionFactorRepository',
    'DatabaseEmissionFactorRepository',
    'CompositeEmissionFactorRepository',
    'ActivityDataRepository',
    'CalculationResultRepository',
    'AuditLogRepository',
    'OrganizationRepository',
    'ExternalEmissionFactorProvider',
    'EPAEmissionFactorProvider',
    'DEFRAEmissionFactorProvider',
]
