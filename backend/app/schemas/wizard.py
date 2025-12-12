# app/schemas/wizard.py
"""
Compliance Wizard Pydantic Schemas.

Provides request/response schemas for the self-serve compliance wizard API.
Enables the "€500 magic moment" - email to compliance report in 10 minutes.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

from app.models.wizard import WizardStatus


# =============================================================================
# VALIDATION PATTERNS
# =============================================================================

# ISO 2-letter country code
COUNTRY_CODE_PATTERN = re.compile(r"^[A-Z]{2}$")

# NACE code: letter + 2-4 digits (e.g., C10, C10.1, C10.11)
NACE_CODE_PATTERN = re.compile(r"^[A-Z]\d{2}(\.\d{1,2})?$")


# =============================================================================
# COMPANY PROFILE SCHEMAS
# =============================================================================

class CompanyProfile(BaseModel):
    """Company profile data collected in Step 1 of the wizard."""
    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    country: str = Field(..., min_length=2, max_length=2, description="ISO 2-letter country code")
    industry_nace: Optional[str] = Field(None, max_length=10, description="NACE industry code (e.g., C10.1)")
    industry_description: Optional[str] = Field(None, max_length=200, description="Industry description if no NACE")
    employees: Optional[int] = Field(None, ge=1, description="Number of employees")
    annual_revenue_eur: Optional[float] = Field(None, ge=0, description="Annual revenue in EUR")
    reporting_year: int = Field(..., ge=2020, le=2030, description="Year being reported on")
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=100)

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        if not COUNTRY_CODE_PATTERN.match(v.upper()):
            raise ValueError("Country must be a 2-letter ISO code")
        return v.upper()

    @field_validator("industry_nace")
    @classmethod
    def validate_nace(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not NACE_CODE_PATTERN.match(v.upper()):
            raise ValueError("NACE code must be letter + 2-4 digits (e.g., C10, C10.11)")
        return v.upper() if v else None


# =============================================================================
# ACTIVITY DATA SCHEMAS
# =============================================================================

class ActivityData(BaseModel):
    """Activity data collected in Step 2 of the wizard."""
    # Scope 1: Direct emissions
    natural_gas_m3: Optional[float] = Field(None, ge=0, description="Natural gas consumption (m³)")
    diesel_l: Optional[float] = Field(None, ge=0, description="Diesel fuel (liters)")
    petrol_l: Optional[float] = Field(None, ge=0, description="Petrol/gasoline (liters)")
    lpg_kg: Optional[float] = Field(None, ge=0, description="LPG consumption (kg)")
    heating_oil_l: Optional[float] = Field(None, ge=0, description="Heating oil (liters)")
    company_vehicles_km: Optional[float] = Field(None, ge=0, description="Company vehicle travel (km)")

    # Scope 2: Indirect emissions (electricity, heat)
    electricity_kwh: Optional[float] = Field(None, ge=0, description="Electricity consumption (kWh)")
    renewable_electricity_kwh: Optional[float] = Field(None, ge=0, description="Renewable electricity (kWh)")
    district_heating_kwh: Optional[float] = Field(None, ge=0, description="District heating (kWh)")
    district_cooling_kwh: Optional[float] = Field(None, ge=0, description="District cooling (kWh)")

    # Scope 3: Value chain emissions
    business_travel_km: Optional[float] = Field(None, ge=0, description="Business travel by air (km)")
    business_travel_rail_km: Optional[float] = Field(None, ge=0, description="Business travel by rail (km)")
    employee_commute_km: Optional[float] = Field(None, ge=0, description="Employee commuting (km)")
    waste_kg: Optional[float] = Field(None, ge=0, description="Waste generated (kg)")
    waste_recycled_kg: Optional[float] = Field(None, ge=0, description="Waste recycled (kg)")
    water_m3: Optional[float] = Field(None, ge=0, description="Water consumption (m³)")

    # Spend-based Scope 3 (EXIOBASE)
    purchased_goods_eur: Optional[float] = Field(None, ge=0, description="Purchased goods & services (EUR)")
    capital_goods_eur: Optional[float] = Field(None, ge=0, description="Capital goods (EUR)")
    upstream_transport_eur: Optional[float] = Field(None, ge=0, description="Upstream transportation (EUR)")

    # Custom activities (for flexibility)
    custom_activities: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional custom activity data as key-value pairs"
    )


# =============================================================================
# CALCULATED EMISSIONS SCHEMAS
# =============================================================================

class EmissionBreakdownItem(BaseModel):
    """Individual emission calculation breakdown."""
    category: str = Field(..., description="Emission category (e.g., 'electricity', 'natural_gas')")
    scope: int = Field(..., ge=1, le=3, description="Scope (1, 2, or 3)")
    activity_value: float = Field(..., description="Input activity value")
    activity_unit: str = Field(..., description="Unit of activity (kWh, km, EUR, etc.)")
    emission_factor: float = Field(..., description="Emission factor used")
    factor_unit: str = Field(..., description="Factor unit (kgCO2e/kWh, etc.)")
    factor_dataset: str = Field(..., description="Dataset source (DEFRA_2024, EXIOBASE_2020, etc.)")
    emissions_kgco2e: float = Field(..., description="Calculated emissions in kgCO2e")
    emissions_tco2e: float = Field(..., description="Calculated emissions in tCO2e")


class CalculatedEmissions(BaseModel):
    """Calculated emissions results."""
    scope1_tco2e: float = Field(default=0.0, ge=0, description="Total Scope 1 emissions (tCO2e)")
    scope2_tco2e: float = Field(default=0.0, ge=0, description="Total Scope 2 emissions (tCO2e)")
    scope3_tco2e: float = Field(default=0.0, ge=0, description="Total Scope 3 emissions (tCO2e)")
    total_tco2e: float = Field(default=0.0, ge=0, description="Total emissions (tCO2e)")
    breakdown: List[EmissionBreakdownItem] = Field(
        default_factory=list,
        description="Detailed breakdown by activity"
    )
    methodology_notes: Optional[str] = Field(
        None,
        description="Notes about calculation methodology and assumptions"
    )
    calculated_at: Optional[datetime] = None


# =============================================================================
# WIZARD SESSION SCHEMAS
# =============================================================================

class WizardSessionCreate(BaseModel):
    """Schema for creating a new wizard session."""
    voucher_code: Optional[str] = Field(None, max_length=50, description="Voucher code to redeem")
    template_id: Optional[str] = Field(None, max_length=50, description="Industry template to use")


class WizardSessionUpdate(BaseModel):
    """Schema for updating a wizard session."""
    current_step: Optional[str] = Field(None, max_length=50)
    company_profile: Optional[CompanyProfile] = None
    activity_data: Optional[ActivityData] = None
    notes: Optional[str] = None


class WizardSessionResponse(BaseModel):
    """Schema for wizard session response."""
    id: int
    tenant_id: str
    voucher_id: Optional[int] = None
    status: WizardStatus
    current_step: str
    company_profile: Optional[Dict[str, Any]] = None
    activity_data: Optional[Dict[str, Any]] = None
    calculated_emissions: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None
    report_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WizardSessionSummary(BaseModel):
    """Summary schema for wizard session list views."""
    id: int
    tenant_id: str
    status: WizardStatus
    current_step: str
    company_name: Optional[str] = None
    total_tco2e: Optional[float] = None
    template_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# INDUSTRY TEMPLATE SCHEMAS
# =============================================================================

class IndustryTemplateResponse(BaseModel):
    """Schema for industry template response."""
    id: str
    name: str
    nace_codes: List[str]
    description: Optional[str] = None
    company_size: Optional[str] = None
    activity_categories: List[str]
    smart_defaults: Optional[Dict[str, Any]] = None
    recommended_datasets: Optional[Dict[str, str]] = None
    display_order: int = 100

    model_config = ConfigDict(from_attributes=True)


class IndustryTemplateCreate(BaseModel):
    """Schema for creating an industry template."""
    id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    nace_codes: List[str] = Field(..., min_items=1)
    description: Optional[str] = None
    company_size: Optional[str] = Field(None, pattern="^(micro|small|medium|large)$")
    activity_categories: List[str] = Field(..., min_items=1)
    smart_defaults: Optional[Dict[str, Any]] = None
    recommended_datasets: Optional[Dict[str, str]] = None
    display_order: int = 100


# =============================================================================
# SMART DEFAULTS SCHEMAS
# =============================================================================

class SmartDefaultsRequest(BaseModel):
    """Request for smart defaults calculation."""
    country: str = Field(..., min_length=2, max_length=2)
    industry_nace: Optional[str] = None
    employees: Optional[int] = Field(None, ge=1)
    annual_revenue_eur: Optional[float] = Field(None, ge=0)
    template_id: Optional[str] = None


class SmartDefaultsResponse(BaseModel):
    """Response with smart defaults for activity data."""
    defaults: Dict[str, float] = Field(
        ...,
        description="Suggested default values for each activity category"
    )
    recommended_datasets: Dict[str, str] = Field(
        ...,
        description="Recommended emission factor datasets by scope"
    )
    methodology: str = Field(
        ...,
        description="Brief explanation of how defaults were calculated"
    )
    confidence: str = Field(
        default="medium",
        description="Confidence level: low, medium, high"
    )


# =============================================================================
# CALCULATION REQUEST/RESPONSE SCHEMAS
# =============================================================================

class CalculateEmissionsRequest(BaseModel):
    """Request to calculate emissions for a wizard session."""
    session_id: int
    recalculate: bool = Field(
        default=False,
        description="If True, recalculate even if already calculated"
    )


class CalculateEmissionsResponse(BaseModel):
    """Response from emissions calculation."""
    session_id: int
    status: str = Field(..., description="success or error")
    emissions: Optional[CalculatedEmissions] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# =============================================================================
# REPORT GENERATION SCHEMAS
# =============================================================================

class GenerateReportRequest(BaseModel):
    """Request to generate a compliance report from wizard session."""
    # Note: session_id is taken from path parameter, not body
    format: str = Field(default="pdf", pattern="^(pdf|xhtml|csv|json)$")
    include_methodology: bool = True
    include_breakdown: bool = True


class GenerateReportResponse(BaseModel):
    """Response from report generation."""
    session_id: int
    report_id: Optional[int] = None
    format: str
    status: str
    file_url: Optional[str] = None
    generated_at: datetime
    errors: List[str] = Field(default_factory=list)
