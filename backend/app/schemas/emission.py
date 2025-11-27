# backend/app/schemas/emission.py
"""
Pydantic schemas for emissions data
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime
from enum import IntEnum


class EmissionScope(IntEnum):
    """GHG Protocol emission scopes"""
    SCOPE_1 = 1
    SCOPE_2 = 2
    SCOPE_3 = 3


class EmissionCreate(BaseModel):
    """Schema for creating emissions"""
    # Required fields
    scope: int = Field(..., ge=1, le=3, description="Emission scope (1, 2, or 3)")
    category: str = Field(..., description="Emission category (e.g., 'Purchased Electricity')")
    activity_type: str = Field(..., description="Type of activity (e.g., 'Electricity', 'Flight')")
    activity_data: float = Field(..., gt=0, description="Activity data amount")
    unit: str = Field(..., description="Unit of measurement (e.g., 'kWh', 'km')")

    # Country code for factor lookup
    country_code: str = Field("GLOBAL", description="ISO country code (e.g., 'DE', 'FR', 'PL') or 'GLOBAL'")

    # Optional manual override
    emission_factor: Optional[float] = Field(None, gt=0, description="Manual emission factor override (kgCO2e/unit)")

    # Optional metadata
    description: Optional[str] = Field(None, description="Additional notes")
    location: Optional[str] = Field(None, description="Location/facility name")
    data_source: Optional[str] = Field(None, description="Data source type")
    calculation_method: Optional[str] = Field(None, description="Calculation method")
    data_quality_score: Optional[float] = Field(None, ge=0, le=100, description="Data quality score (0-100)")
    reporting_period: Optional[str] = Field(None, description="Reporting period (e.g., '2024-Q1')")


class EmissionUpdate(BaseModel):
    """Schema for updating emissions"""
    scope: Optional[int] = Field(None, ge=1, le=3)
    category: Optional[str] = None
    activity_type: Optional[str] = None
    activity_data: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = None
    country_code: Optional[str] = None
    emission_factor: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    location: Optional[str] = None
    data_source: Optional[str] = None


class EmissionResponse(BaseModel):
    """Schema for emission responses"""
    id: int
    scope: int
    category: str
    activity_type: Optional[str] = None
    activity_data: float
    unit: str
    country_code: Optional[str] = None
    emission_factor: Optional[float] = None
    amount: float = Field(..., description="Calculated emission amount in tCO2e")
    description: Optional[str] = None
    location: Optional[str] = None
    data_quality_score: Optional[float] = None
    uncertainty_percentage: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EmissionsSummary(BaseModel):
    """Schema for emissions summary"""
    scope1_total: float = Field(0, description="Total Scope 1 emissions")
    scope2_total: float = Field(0, description="Total Scope 2 emissions")
    scope3_total: float = Field(0, description="Total Scope 3 emissions")
    total_emissions: float = Field(0, description="Total emissions across all scopes")
    by_category: Dict[str, float] = Field(default_factory=dict, description="Emissions by category")

    model_config = ConfigDict(from_attributes=True)
