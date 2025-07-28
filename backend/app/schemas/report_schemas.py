"""
Report-related schemas for GHG Protocol Scope 3 Calculator
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Union, Any
from uuid import UUID

from pydantic import Field, conint

from app.models.ghg_protocol_models import Scope3Category, Scope3Inventory
from app.schemas.base_schemas import BaseRequest, BaseResponse
from app.schemas.calculation_schemas import EmissionResultResponse


class ReportGenerationRequest(BaseRequest):
    """Request to generate compliance report"""
    report_type: str = Field(..., pattern="^(CDP|TCFD|CSRD|GRI|CUSTOM)$")
    year: conint(ge=2000, le=2100)
    include_categories: Optional[List[Scope3Category]] = None
    format: str = Field("pdf", pattern="^(pdf|xlsx|json)$")
    options: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "report_type": "CDP",
                "year": 2024,
                "format": "pdf",
                "options": {
                    "include_methodology": True,
                    "include_uncertainties": True
                }
            }
        }


class ReportResponse(BaseResponse):
    """Report generation response"""
    report_id: UUID
    report_type: str
    status: str
    download_url: str
    expires_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InventoryResponse(BaseResponse):
    """Complete Scope 3 inventory"""
    id: UUID
    reporting_year: int
    calculation_date: datetime
    total_emissions: EmissionResultResponse
    emissions_by_category: Dict[str, EmissionResultResponse]
    completeness: float = Field(..., ge=0, le=1)
    average_data_quality: float = Field(..., ge=1, le=5)
    
    # Compliance
    ghg_protocol_compliant: bool
    iso_14064_compliant: bool
    third_party_verified: bool
    verification_statement: Optional[str] = None
    
    # Key insights
    largest_categories: List[Dict[str, Union[str, float]]]
    year_over_year_change: Optional[float] = None
    vs_baseline: Optional[float] = None
    
    @classmethod
    def from_domain(cls, inventory: Scope3Inventory) -> "InventoryResponse":
        # Calculate largest categories
        sorted_categories = sorted(
            inventory.emissions_by_category.items(),
            key=lambda x: x[1].value,
            reverse=True
        )[:5]
        
        largest = [
            {
                "category": cat.value,
                "emissions": float(em.value),
                "percentage": float(em.value / inventory.total_emissions.value * 100)
            }
            for cat, em in sorted_categories
        ]
        
        return cls(
            id=inventory.id,
            reporting_year=inventory.reporting_year,
            calculation_date=inventory.calculation_date,
            total_emissions=EmissionResultResponse.from_domain(inventory.total_emissions),
            emissions_by_category={
                cat.value: EmissionResultResponse.from_domain(em)
                for cat, em in inventory.emissions_by_category.items()
            },
            completeness=inventory.completeness,
            average_data_quality=inventory.average_data_quality,
            ghg_protocol_compliant=inventory.ghg_protocol_compliant,
            iso_14064_compliant=inventory.iso_14064_compliant,
            third_party_verified=inventory.third_party_verified,
            verification_statement=inventory.verification_statement,
            largest_categories=largest
        )
