"""
GHG Protocol Scope 3 Calculator API Schemas
"""

# Import all schemas from ghg_schemas for convenience
from app.schemas.ghg_schemas import *

# Also make individual schema modules available
from app.schemas import (
    base_schemas,
    calculation_schemas,
    emission_factor_schemas,
    activity_data_schemas,
    report_schemas,
    analytics_schemas,
    organization_schemas,
    batch_schemas,
    audit_schemas,
)

__all__ = [
    # Re-export everything from ghg_schemas
    'BaseRequest', 'BaseResponse', 'PaginatedResponse',
    'HealthCheckResponse', 'ErrorResponse', 'ValidationErrorResponse',
    'ActivityDataPoint', 'CalculationRequest', 'CalculationResponse',
    'EmissionResultResponse', 'CategoryCalculationResponse',
    'CalculationProgressMessage',
    'EmissionFactorCreateRequest', 'EmissionFactorResponse',
    'ActivityDataUploadRequest', 'BulkActivityDataRequest',
    'ReportGenerationRequest', 'ReportResponse', 'InventoryResponse',
    'AnalyticsMetric', 'AnalyticsResponse',
    'OrganizationResponse',
    'BatchCalculationRequest', 'BatchCalculationResponse',
    'DataExportRequest', 'DataImportRequest',
    'AuditLogResponse', 'AuditTrailRequest', 'ValidationRuleSet',
    
    # Schema modules
    'base_schemas',
    'calculation_schemas',
    'emission_factor_schemas',
    'activity_data_schemas',
    'report_schemas',
    'analytics_schemas',
    'organization_schemas',
    'batch_schemas',
    'audit_schemas',
]
