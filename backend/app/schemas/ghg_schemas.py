"""
Main GHG Protocol schemas - imports from specialized schema files
"""
from pydantic import Field
from app.models.ghg_protocol_models import Scope3Category
from app.models.ghg_protocol_models import EmissionFactorSource
# Import all schemas for backward compatibility and convenience
from app.schemas.base_schemas import (
    BaseRequest, BaseResponse, PaginatedResponse, 
    HealthCheckResponse, ErrorResponse, ValidationErrorResponse
)
from app.schemas.calculation_schemas import (
    ActivityDataPoint, CalculationRequest, CalculationResponse,
    EmissionResultResponse, CategoryCalculationResponse,
    CalculationProgressMessage)
from app.schemas.emission_factor_schemas import (
    EmissionFactorCreateRequest, EmissionFactorResponse)
from app.schemas.activity_data_schemas import (
    ActivityDataUploadRequest, BulkActivityDataRequest)
from app.schemas.report_schemas import (
    ReportGenerationRequest, ReportResponse, InventoryResponse)
from app.schemas.analytics_schemas import (
    AnalyticsMetric, AnalyticsResponse)
from app.schemas.organization_schemas import (
    OrganizationResponse)
from app.schemas.batch_schemas import (
    BatchCalculationRequest, BatchCalculationResponse,
    DataExportRequest, DataImportRequest)
from app.schemas.audit_schemas import (
    AuditLogResponse, AuditTrailRequest, ValidationRuleSet)
# Re-export all for convenience
__all__ = [
    # Base
    'BaseRequest', 'BaseResponse', 'PaginatedResponse',
    'HealthCheckResponse', 'ErrorResponse', 'ValidationErrorResponse',
    
    # Calculation
    'ActivityDataPoint', 'CalculationRequest', 'CalculationResponse',
    'EmissionResultResponse', 'CategoryCalculationResponse',
    'CalculationProgressMessage',
    # Emission Factors
    'EmissionFactorCreateRequest', 'EmissionFactorResponse',
    # Activity Data
    'ActivityDataUploadRequest', 'BulkActivityDataRequest',
    # Reports
    'ReportGenerationRequest', 'ReportResponse', 'InventoryResponse',
    # Analytics
    'AnalyticsMetric', 'AnalyticsResponse',
    # Organization
    'OrganizationResponse',
    # Batch Operations
    'BatchCalculationRequest', 'BatchCalculationResponse',
    'DataExportRequest', 'DataImportRequest',
    # Audit
    'AuditLogResponse', 'AuditTrailRequest', 'ValidationRuleSet',
]
# Legacy compatibility - if your code uses these old names
# TODO: Remove these aliases after updating all imports
ActivityDataInput = ActivityDataPoint
EmissionFactorQuery = EmissionFactorCreateRequest
ReportRequest = ReportGenerationRequest
# Add this for backwards compatibility with existing code
# that might be importing from ghg_schemas
from typing import Any as _Any, Optional
# Create a simple EmissionFactorQuery if it doesn't exist
class EmissionFactorQuery(BaseRequest):
    """Query parameters for emission factor search"""
    category: Optional[Scope3Category] = None
    region: Optional[str] = None
    year: Optional[int] = None
    source: Optional[EmissionFactorSource] = None
    search: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
