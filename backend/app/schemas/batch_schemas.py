"""
Batch operation schemas for GHG Protocol Scope 3 Calculator
"""

from datetime import date
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import Field

from app.models.ghg_protocol_models import Scope3Category, MethodologyType
from app.schemas.base_schemas import BaseRequest, BaseResponse


class BatchCalculationRequest(BaseRequest):
    """Request to calculate multiple categories"""
    categories: List[Scope3Category] = Field(..., min_items=1, max_items=15)
    methodology: MethodologyType = MethodologyType.HYBRID
    reporting_period: date
    use_cached_data: bool = True
    priority: str = Field("normal", pattern="^(low|normal|high)$")


class BatchCalculationResponse(BaseResponse):
    """Response for batch calculation"""
    batch_id: UUID
    total_categories: int
    status: str
    submitted_calculations: List[UUID]
    estimated_completion_time: int  # seconds


class DataExportRequest(BaseRequest):
    """Request to export data"""
    export_type: str = Field(..., pattern="^(activity_data|emission_factors|calculations|full_backup)$")
    categories: Optional[List[Scope3Category]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    format: str = Field("json", pattern="^(json|csv|xlsx)$")
    include_metadata: bool = True


class DataImportRequest(BaseRequest):
    """Request to import data"""
    import_type: str = Field(..., pattern="^(activity_data|emission_factors)$")
    format: str = Field(..., pattern="^(json|csv|xlsx)$")
    file_url: str
    mapping: Optional[Dict[str, str]] = None
    validation_mode: str = Field("strict", pattern="^(strict|lenient|skip)$")
