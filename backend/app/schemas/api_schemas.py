"""
API Schemas for FactorTrace Scope 3 Compliance Tool
Pydantic models for request/response validation
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field, field_validator


# --- Voucher Schemas ---------------------------------------------------------

class VoucherInput(BaseModel):
    """Input schema for voucher generation - used by tests"""
    supplier_id: str = Field(..., description="Unique supplier identifier")
    supplier_name: str = Field(..., description="Supplier company name")
    legal_entity_identifier: str = Field(..., description="Legal entity ID (e.g., LEI)")
    product_category: str = Field(..., description="Product category code")
    cost: float = Field(..., gt=0, description="Transaction cost")
    material_type: str = Field(..., description="Material type classification")
    origin_country: str = Field(..., description="ISO country code of origin")
    emission_factor: float = Field(..., gt=0, description="Emission factor value")
    fallback_factor_used: bool = Field(False, description="Whether fallback factor was used")
    
    # Additional optional fields for comprehensive vouchers
    calculation_date: Optional[date] = Field(None, description="Date of calculation")
    data_quality_rating: Optional[float] = Field(None, ge=0, le=1, description="Data quality score")
    verification_status: Optional[str] = Field(None, description="Verification status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "supplier_id": "SUP-12345",
                "supplier_name": "Green Materials Co.",
                "legal_entity_identifier": "549300EXAMPLE123456",
                "product_category": "raw_materials",
                "cost": 10000.0,
                "material_type": "steel",
                "origin_country": "DE",
                "emission_factor": 2.45,
                "fallback_factor_used": False
            }
        }


class VoucherOutput(BaseModel):
    """Output schema for voucher generation"""
    voucher_id: str = Field(..., description="Unique voucher identifier")
    xml_content: str = Field(..., description="Generated XML voucher content")
    validation_status: str = Field("valid", description="XML validation status")
    generated_at: datetime = Field(..., description="Timestamp of generation")
    checksum: Optional[str] = Field(None, description="XML content checksum")


# --- Emissions Calculation Schemas -------------------------------------------

class EmissionFactorInput(BaseModel):
    """Schema for emission factor specification"""
    factor_id: Optional[str] = Field(None, description="Factor ID from database")
    factor_value: Optional[float] = Field(None, gt=0, description="Direct factor value")
    factor_unit: Optional[str] = Field(None, description="Factor unit (e.g., kgCO2e/kWh)")
    source: Optional[str] = Field(None, description="Factor source (e.g., 'DEFRA', 'EPA')")
    
    @field_validator('factor_id', 'factor_value')
    @classmethod
    def validate_factor_specification(cls, v, values):
        """Ensure either factor_id or factor_value is provided"""
        if not v and not values.get('factor_value') and not values.get('factor_id'):
            raise ValueError("Either factor_id or factor_value must be provided")
        return v


class ActivityDataInput(BaseModel):
    """Schema for activity data input"""
    activity_type: str = Field(..., description="Type of activity")
    quantity: float = Field(..., gt=0, description="Activity quantity")
    unit: str = Field(..., description="Unit of measurement")
    period_start: Optional[date] = Field(None, description="Activity period start")
    period_end: Optional[date] = Field(None, description="Activity period end")
    location: Optional[str] = Field(None, description="Activity location/region")
    
    @field_validator('period_end')
    @classmethod
    def validate_period(cls, v, values):
        """Ensure period_end is after period_start"""
        start = values.get('period_start')
        if start and v and v < start:
            raise ValueError("period_end must be after period_start")
        return v


class EmissionCalculationInput(BaseModel):
    """Comprehensive input schema for emissions calculation"""
    activity_data: ActivityDataInput
    emission_factor: EmissionFactorInput
    scope: str = Field(..., pattern="^[123]$", description="GHG Protocol scope")
    scope3_category: Optional[int] = Field(None, ge=1, le=15, description="Scope 3 category (1-15)")
    calculation_method: str = Field("quantity", pattern="^(quantity|spend|distance|hybrid)$")
    uncertainty_range: Optional[Dict[str, float]] = Field(None, description="Uncertainty bounds")
    
    @field_validator('scope3_category')
    @classmethod
    def validate_scope3_category(cls, v, values):
        """Validate scope3_category is required when scope is 3"""
        scope = values.get('scope')
        if scope == '3' and not v:
            raise ValueError("scope3_category is required when scope is 3")
        return v


class EmissionCalculationOutput(BaseModel):
    """Output schema for emissions calculation"""
    total_emissions: float = Field(..., description="Total calculated emissions in tCO2e")
    emissions_by_gas: Optional[Dict[str, float]] = Field(None, description="Breakdown by GHG type")
    calculation_method: str = Field(..., description="Method used for calculation")
    activity_data_used: Dict[str, Any] = Field(..., description="Activity data summary")
    emission_factor_used: Dict[str, Any] = Field(..., description="Emission factor details")
    uncertainty: Optional[Dict[str, float]] = Field(None, description="Uncertainty metrics")
    data_quality_indicators: Optional[Dict[str, Any]] = Field(None, description="DQI scores")
    calculation_timestamp: datetime = Field(..., description="Calculation timestamp")


# --- Batch Processing Schemas ------------------------------------------------

class BatchVoucherInput(BaseModel):
    """Schema for batch voucher generation"""
    vouchers: List[VoucherInput] = Field(..., min_items=1, max_items=1000)
    batch_metadata: Optional[Dict[str, Any]] = Field(None, description="Batch-level metadata")
    validation_mode: str = Field("strict", pattern="^(strict|lenient)$")


class BatchCalculationInput(BaseModel):
    """Schema for batch emissions calculation"""
    calculations: List[EmissionCalculationInput] = Field(..., min_items=1, max_items=1000)
    aggregation_method: str = Field("sum", pattern="^(sum|average|weighted)$")
    group_by: Optional[List[str]] = Field(None, description="Fields to group results by")


# --- Error Response Schemas --------------------------------------------------

class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ErrorResponse(BaseModel):
    """Standard error response"""
    status: Literal["error"] = "error"
    errors: List[ErrorDetail] = Field(..., min_items=1)
    request_id: Optional[str] = Field(None, description="Request tracking ID")
    timestamp: datetime = Field(..., description="Error timestamp")


# --- Validation Utilities ----------------------------------------------------

def validate_emission_factor_range(value: float, factor_type: str) -> float:
    """Validate emission factor is within reasonable range"""
    ranges = {
        "electricity": (0.001, 2.0),  # kgCO2e/kWh
        "fuel": (0.1, 5.0),  # kgCO2e/L or kgCO2e/kg
        "material": (0.01, 50.0),  # kgCO2e/kg
        "transport": (0.001, 1.0),  # kgCO2e/km
        "waste": (0.01, 5.0),  # kgCO2e/kg
    }
    
    min_val, max_val = ranges.get(factor_type, (0.001, 100.0))
    if not min_val <= value <= max_val:
        raise ValueError(
            f"Emission factor {value} outside reasonable range "
            f"[{min_val}, {max_val}] for {factor_type}"
        )
    
    return value


# --- Type Aliases ------------------------------------------------------------

VoucherRequest = VoucherInput  # Alias for backward compatibility
EmissionsRequest = EmissionCalculationInput  # Alias for backward compatibility