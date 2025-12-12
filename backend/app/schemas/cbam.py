# app/schemas/cbam.py
"""
CBAM (Carbon Border Adjustment Mechanism) Pydantic Schemas.

Provides request/response schemas for CBAM API endpoints.

Reference: docs/regimes/cbam.md
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

from app.models.cbam import (
    CBAMDeclarationStatus,
    CBAMFactorDataset,
    CBAMProductSector,
)


# =============================================================================
# VALIDATION PATTERNS
# =============================================================================

# CN code: 8-10 digits
CN_CODE_PATTERN = re.compile(r"^\d{8,10}$")

# HS code: 4-8 digits (HS system uses 4 for heading, 6 for subheading, 8 for national)
HS_CODE_PATTERN = re.compile(r"^\d{4,8}$")

# EORI: 2-letter country code + up to 15 chars
EORI_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{1,15}$")

# ISO 2-letter country code
COUNTRY_CODE_PATTERN = re.compile(r"^[A-Z]{2}$")


# =============================================================================
# CBAM FACTOR SOURCE SCHEMAS
# =============================================================================

class CBAMFactorSourceBase(BaseModel):
    """Base schema for CBAM factor source."""
    dataset: CBAMFactorDataset
    version: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    source_url: Optional[str] = Field(None, max_length=500)
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class CBAMFactorSourceCreate(CBAMFactorSourceBase):
    """Schema for creating a CBAM factor source."""
    pass


class CBAMFactorSourceResponse(CBAMFactorSourceBase):
    """Schema for CBAM factor source response."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# CBAM PRODUCT SCHEMAS
# =============================================================================

class CBAMProductBase(BaseModel):
    """Base schema for CBAM product."""
    cn_code: str = Field(..., min_length=8, max_length=10, description="Combined Nomenclature code (8-10 digits)")
    description: str = Field(..., min_length=1, max_length=500)
    sector: CBAMProductSector
    unit: str = Field(default="tonne", max_length=20)
    hs_code: Optional[str] = Field(None, max_length=6, description="Harmonized System code (6 digits)")
    notes: Optional[str] = None
    is_active: bool = True

    @field_validator("cn_code")
    @classmethod
    def validate_cn_code(cls, v: str) -> str:
        if not CN_CODE_PATTERN.match(v):
            raise ValueError("CN code must be 8-10 digits")
        return v

    @field_validator("hs_code")
    @classmethod
    def validate_hs_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not HS_CODE_PATTERN.match(v):
            raise ValueError("HS code must be 4-8 digits")
        return v


class CBAMProductCreate(CBAMProductBase):
    """Schema for creating a CBAM product."""
    default_factor_id: Optional[int] = None


class CBAMProductUpdate(BaseModel):
    """Schema for updating a CBAM product."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    sector: Optional[CBAMProductSector] = None
    unit: Optional[str] = Field(None, max_length=20)
    hs_code: Optional[str] = Field(None, max_length=6)
    default_factor_id: Optional[int] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class CBAMProductResponse(CBAMProductBase):
    """Schema for CBAM product response."""
    id: int
    default_factor_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# CBAM INSTALLATION SCHEMAS (Tenant-owned)
# =============================================================================

class CBAMInstallationBase(BaseModel):
    """Base schema for CBAM installation."""
    installation_id: str = Field(..., min_length=1, max_length=100, description="External installation identifier")
    name: str = Field(..., min_length=1, max_length=200)
    country: str = Field(..., min_length=2, max_length=2, description="ISO 2-letter country code")
    region: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    operator_name: Optional[str] = Field(None, max_length=200)
    operator_id: Optional[str] = Field(None, max_length=100)
    sector: CBAMProductSector
    specific_emission_factor: Optional[float] = Field(None, ge=0, description="Plant-specific emission factor (tCO2e per unit)")
    specific_factor_unit: Optional[str] = Field(None, max_length=50)
    specific_factor_valid_from: Optional[datetime] = None
    specific_factor_valid_to: Optional[datetime] = None
    is_verified: bool = False
    verification_body: Optional[str] = Field(None, max_length=200)
    verification_date: Optional[datetime] = None
    verification_reference: Optional[str] = Field(None, max_length=200)
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        if not COUNTRY_CODE_PATTERN.match(v.upper()):
            raise ValueError("Country must be a 2-letter ISO code")
        return v.upper()


class CBAMInstallationCreate(CBAMInstallationBase):
    """Schema for creating a CBAM installation."""
    pass


class CBAMInstallationUpdate(BaseModel):
    """Schema for updating a CBAM installation."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    region: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    operator_name: Optional[str] = Field(None, max_length=200)
    operator_id: Optional[str] = Field(None, max_length=100)
    specific_emission_factor: Optional[float] = Field(None, ge=0)
    specific_factor_unit: Optional[str] = Field(None, max_length=50)
    specific_factor_valid_from: Optional[datetime] = None
    specific_factor_valid_to: Optional[datetime] = None
    is_verified: Optional[bool] = None
    verification_body: Optional[str] = Field(None, max_length=200)
    verification_date: Optional[datetime] = None
    verification_reference: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CBAMInstallationResponse(CBAMInstallationBase):
    """Schema for CBAM installation response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# CBAM DECLARATION LINE SCHEMAS
# =============================================================================

class CBAMDeclarationLineBase(BaseModel):
    """Base schema for CBAM declaration line."""
    cbam_product_id: int = Field(..., description="FK to CBAM product")
    country_of_origin: str = Field(..., min_length=2, max_length=2, description="ISO 2-letter country code")
    facility_id: Optional[str] = Field(None, max_length=100)
    facility_name: Optional[str] = Field(None, max_length=200)
    quantity: float = Field(..., gt=0, description="Quantity of goods imported")
    quantity_unit: str = Field(default="tonne", max_length=20)

    @field_validator("country_of_origin")
    @classmethod
    def validate_country_of_origin(cls, v: str) -> str:
        if not COUNTRY_CODE_PATTERN.match(v.upper()):
            raise ValueError("Country of origin must be a 2-letter ISO code")
        return v.upper()


class CBAMDeclarationLineCreate(CBAMDeclarationLineBase):
    """Schema for creating a CBAM declaration line."""
    # Optional: allow manual factor override
    emission_factor_value: Optional[float] = Field(None, ge=0, description="Manual emission factor override")
    emission_factor_unit: Optional[str] = Field(None, max_length=50)
    factor_dataset: Optional[CBAMFactorDataset] = None
    evidence_reference: Optional[str] = Field(None, max_length=500)
    calculation_notes: Optional[str] = None


class CBAMDeclarationLineUpdate(BaseModel):
    """Schema for updating a CBAM declaration line."""
    quantity: Optional[float] = Field(None, gt=0)
    quantity_unit: Optional[str] = Field(None, max_length=20)
    facility_id: Optional[str] = Field(None, max_length=100)
    facility_name: Optional[str] = Field(None, max_length=200)
    evidence_reference: Optional[str] = Field(None, max_length=500)
    calculation_notes: Optional[str] = None


class CBAMDeclarationLineResponse(CBAMDeclarationLineBase):
    """Schema for CBAM declaration line response."""
    id: int
    declaration_id: int
    embedded_emissions_tco2e: Optional[float] = None
    emission_factor_value: Optional[float] = None
    emission_factor_unit: Optional[str] = None
    emission_factor_id: Optional[int] = None
    factor_dataset: Optional[CBAMFactorDataset] = None
    is_default_factor: bool = True
    evidence_reference: Optional[str] = None
    evidence_document_id: Optional[int] = None
    calculation_date: Optional[datetime] = None
    calculation_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Include product details for convenience
    product: Optional[CBAMProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# CBAM DECLARATION SCHEMAS (Tenant-owned)
# =============================================================================

class CBAMDeclarationBase(BaseModel):
    """Base schema for CBAM declaration."""
    declaration_reference: Optional[str] = Field(None, max_length=100, description="User-supplied or auto-generated reference")
    period_start: datetime = Field(..., description="Start of reporting period")
    period_end: datetime = Field(..., description="End of reporting period")
    importer_name: Optional[str] = Field(None, max_length=200)
    importer_eori: Optional[str] = Field(None, max_length=17, description="EORI number")
    importer_country: Optional[str] = Field(None, max_length=2, description="ISO 2-letter country code")

    @field_validator("importer_eori")
    @classmethod
    def validate_eori(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not EORI_PATTERN.match(v.upper()):
            raise ValueError("EORI must be 2-letter country code followed by up to 15 alphanumeric characters")
        return v.upper() if v else None

    @field_validator("importer_country")
    @classmethod
    def validate_importer_country(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not COUNTRY_CODE_PATTERN.match(v.upper()):
            raise ValueError("Importer country must be a 2-letter ISO code")
        return v.upper() if v else None


class CBAMDeclarationCreate(CBAMDeclarationBase):
    """Schema for creating a CBAM declaration."""
    # Optionally include lines during creation
    lines: Optional[List[CBAMDeclarationLineCreate]] = None


class CBAMDeclarationUpdate(BaseModel):
    """Schema for updating a CBAM declaration."""
    declaration_reference: Optional[str] = Field(None, max_length=100)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    importer_name: Optional[str] = Field(None, max_length=200)
    importer_eori: Optional[str] = Field(None, max_length=17)
    importer_country: Optional[str] = Field(None, max_length=2)
    status: Optional[CBAMDeclarationStatus] = None


class CBAMDeclarationResponse(CBAMDeclarationBase):
    """Schema for CBAM declaration response."""
    id: int
    tenant_id: str
    status: CBAMDeclarationStatus
    total_embedded_emissions_tco2e: float = 0.0
    total_quantity: float = 0.0
    is_verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    submitted_at: Optional[datetime] = None
    submission_reference: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = None

    # Include lines for full declaration view
    lines: Optional[List[CBAMDeclarationLineResponse]] = None
    line_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CBAMDeclarationSummary(BaseModel):
    """Summary schema for CBAM declaration list views."""
    id: int
    tenant_id: str
    declaration_reference: Optional[str] = None
    period_start: datetime
    period_end: datetime
    status: CBAMDeclarationStatus
    total_embedded_emissions_tco2e: float = 0.0
    total_quantity: float = 0.0
    line_count: int = 0
    importer_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# CALCULATION REQUEST/RESPONSE SCHEMAS
# =============================================================================

class CBAMCalculateRequest(BaseModel):
    """Request schema for triggering CBAM emissions calculation."""
    declaration_id: int
    recalculate_all: bool = Field(
        default=False,
        description="If True, recalculate all lines; if False, only calculate lines without emissions"
    )


class CBAMCalculationResult(BaseModel):
    """Result of a single line calculation."""
    line_id: int
    cbam_product_id: int
    quantity: float
    embedded_emissions_tco2e: float
    emission_factor_value: float
    emission_factor_unit: str
    factor_dataset: CBAMFactorDataset
    is_default_factor: bool


class CBAMCalculateResponse(BaseModel):
    """Response schema for CBAM calculation."""
    declaration_id: int
    total_embedded_emissions_tco2e: float
    total_quantity: float
    lines_calculated: int
    lines_skipped: int
    results: List[CBAMCalculationResult]
    errors: List[str] = []


# =============================================================================
# EXPORT/REPORT SCHEMAS
# =============================================================================

class CBAMExportRequest(BaseModel):
    """Request schema for CBAM report export."""
    declaration_id: int
    format: str = Field(default="pdf", description="Export format: pdf, xhtml, csv")
    include_line_details: bool = True


class CBAMExportResponse(BaseModel):
    """Response schema for CBAM export."""
    declaration_id: int
    format: str
    file_url: Optional[str] = None
    file_content: Optional[str] = None  # Base64 encoded for inline response
    generated_at: datetime


# =============================================================================
# AGGREGATION SCHEMAS
# =============================================================================

class CBAMProductBreakdown(BaseModel):
    """Emissions breakdown by product."""
    cbam_product_id: int
    cn_code: str
    sector: CBAMProductSector
    total_quantity: float
    total_emissions_tco2e: float
    line_count: int
    default_factor_percentage: float = Field(description="Percentage of emissions using default factors")


class CBAMCountryBreakdown(BaseModel):
    """Emissions breakdown by country of origin."""
    country_of_origin: str
    total_quantity: float
    total_emissions_tco2e: float
    line_count: int
    products: List[str] = Field(default_factory=list, description="CN codes of products from this country")


class CBAMDeclarationBreakdown(BaseModel):
    """Detailed breakdown of a CBAM declaration."""
    declaration_id: int
    total_embedded_emissions_tco2e: float
    total_quantity: float
    by_product: List[CBAMProductBreakdown]
    by_country: List[CBAMCountryBreakdown]
    by_factor_dataset: dict[str, float]  # dataset -> total emissions
