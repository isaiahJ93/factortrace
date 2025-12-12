# app/schemas/eudr.py
"""
EUDR (EU Deforestation Regulation) Pydantic Schemas.

Provides request/response schemas for EUDR API endpoints.

Reference: docs/regimes/eudr.md
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re

from app.models.eudr import (
    EUDRCommodityType,
    EUDROperatorRole,
    EUDRSupplyChainLinkType,
    EUDRRiskLevel,
    EUDRDueDiligenceStatus,
    EUDRGeoRiskSource,
)


# =============================================================================
# VALIDATION PATTERNS
# =============================================================================

# ISO 2-letter country code
COUNTRY_CODE_PATTERN = re.compile(r"^[A-Z]{2}$")

# HS code: 6-10 digits
HS_CODE_PATTERN = re.compile(r"^\d{6,10}$")

# Latitude: -90 to 90
LATITUDE_MIN = -90.0
LATITUDE_MAX = 90.0

# Longitude: -180 to 180
LONGITUDE_MIN = -180.0
LONGITUDE_MAX = 180.0


# =============================================================================
# EUDR COMMODITY SCHEMAS (Global Reference Data)
# =============================================================================

class EUDRCommodityBase(BaseModel):
    """Base schema for EUDR commodity."""
    name: str = Field(..., min_length=1, max_length=100)
    commodity_type: EUDRCommodityType
    description: Optional[str] = Field(None, max_length=500)
    hs_code: Optional[str] = Field(None, max_length=10, description="HS code (6-10 digits)")
    risk_profile_default: EUDRRiskLevel = EUDRRiskLevel.MEDIUM
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator("hs_code")
    @classmethod
    def validate_hs_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not HS_CODE_PATTERN.match(v):
            raise ValueError("HS code must be 6-10 digits")
        return v


class EUDRCommodityCreate(EUDRCommodityBase):
    """Schema for creating an EUDR commodity."""
    pass


class EUDRCommodityUpdate(BaseModel):
    """Schema for updating an EUDR commodity."""
    description: Optional[str] = Field(None, max_length=500)
    hs_code: Optional[str] = Field(None, max_length=10)
    risk_profile_default: Optional[EUDRRiskLevel] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class EUDRCommodityResponse(EUDRCommodityBase):
    """Schema for EUDR commodity response."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# EUDR OPERATOR SCHEMAS (Tenant-owned)
# =============================================================================

class EUDROperatorBase(BaseModel):
    """Base schema for EUDR operator."""
    name: str = Field(..., min_length=1, max_length=200)
    role: EUDROperatorRole
    country: str = Field(..., min_length=2, max_length=2, description="ISO 2-letter country code")
    identifier: Optional[str] = Field(None, max_length=100, description="VAT/registration ID")
    address: Optional[str] = None
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        if not COUNTRY_CODE_PATTERN.match(v.upper()):
            raise ValueError("Country must be a 2-letter ISO code")
        return v.upper()


class EUDROperatorCreate(EUDROperatorBase):
    """Schema for creating an EUDR operator."""
    pass


class EUDROperatorUpdate(BaseModel):
    """Schema for updating an EUDR operator."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    role: Optional[EUDROperatorRole] = None
    identifier: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class EUDROperatorResponse(EUDROperatorBase):
    """Schema for EUDR operator response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# EUDR SUPPLY SITE SCHEMAS (Tenant-owned)
# =============================================================================

class EUDRSupplySiteBase(BaseModel):
    """Base schema for EUDR supply site."""
    operator_id: int = Field(..., description="FK to operator")
    commodity_id: int = Field(..., description="FK to commodity")
    name: str = Field(..., min_length=1, max_length=200)
    site_reference: Optional[str] = Field(None, max_length=100)
    country: str = Field(..., min_length=2, max_length=2, description="ISO 2-letter country code")
    region: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=LATITUDE_MIN, le=LATITUDE_MAX, description="Centroid latitude")
    longitude: Optional[float] = Field(None, ge=LONGITUDE_MIN, le=LONGITUDE_MAX, description="Centroid longitude")
    geometry_geojson: Optional[str] = Field(None, description="Site boundary as GeoJSON polygon")
    area_ha: Optional[float] = Field(None, ge=0, description="Site area in hectares")
    legal_title_reference: Optional[str] = Field(None, max_length=200)
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        if not COUNTRY_CODE_PATTERN.match(v.upper()):
            raise ValueError("Country must be a 2-letter ISO code")
        return v.upper()


class EUDRSupplySiteCreate(EUDRSupplySiteBase):
    """Schema for creating an EUDR supply site."""
    pass


class EUDRSupplySiteUpdate(BaseModel):
    """Schema for updating an EUDR supply site."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    site_reference: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=LATITUDE_MIN, le=LATITUDE_MAX)
    longitude: Optional[float] = Field(None, ge=LONGITUDE_MIN, le=LONGITUDE_MAX)
    geometry_geojson: Optional[str] = None
    area_ha: Optional[float] = Field(None, ge=0)
    legal_title_reference: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class EUDRSupplySiteResponse(EUDRSupplySiteBase):
    """Schema for EUDR supply site response."""
    id: int
    tenant_id: str
    has_coordinates: bool = False
    has_polygon: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Include related data
    commodity: Optional[EUDRCommodityResponse] = None
    operator: Optional[EUDROperatorResponse] = None

    model_config = ConfigDict(from_attributes=True)


class EUDRSupplySiteSummary(BaseModel):
    """Summary schema for supply site list views."""
    id: int
    tenant_id: str
    name: str
    country: str
    commodity_id: int
    operator_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_ha: Optional[float] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# EUDR BATCH SCHEMAS (Tenant-owned)
# =============================================================================

class EUDRBatchBase(BaseModel):
    """Base schema for EUDR batch."""
    batch_reference: str = Field(..., min_length=1, max_length=100)
    commodity_id: int = Field(..., description="FK to commodity")
    volume: float = Field(..., gt=0, description="Quantity of commodity")
    volume_unit: str = Field(default="tonne", max_length=20)
    harvest_year: Optional[int] = Field(None, ge=1900, le=2100)
    origin_site_id: Optional[int] = Field(None, description="FK to origin supply site")
    origin_country: str = Field(..., min_length=2, max_length=2, description="Country of origin")
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator("origin_country")
    @classmethod
    def validate_origin_country(cls, v: str) -> str:
        if not COUNTRY_CODE_PATTERN.match(v.upper()):
            raise ValueError("Origin country must be a 2-letter ISO code")
        return v.upper()


class EUDRBatchCreate(EUDRBatchBase):
    """Schema for creating an EUDR batch."""
    pass


class EUDRBatchUpdate(BaseModel):
    """Schema for updating an EUDR batch."""
    batch_reference: Optional[str] = Field(None, min_length=1, max_length=100)
    volume: Optional[float] = Field(None, gt=0)
    volume_unit: Optional[str] = Field(None, max_length=20)
    harvest_year: Optional[int] = Field(None, ge=1900, le=2100)
    origin_site_id: Optional[int] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class EUDRBatchResponse(EUDRBatchBase):
    """Schema for EUDR batch response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Include related data
    commodity: Optional[EUDRCommodityResponse] = None
    origin_site: Optional[EUDRSupplySiteSummary] = None

    model_config = ConfigDict(from_attributes=True)


class EUDRBatchSummary(BaseModel):
    """Summary schema for batch list views."""
    id: int
    tenant_id: str
    batch_reference: str
    commodity_id: int
    volume: float
    volume_unit: str
    harvest_year: Optional[int] = None
    origin_country: str
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# EUDR SUPPLY CHAIN LINK SCHEMAS (Tenant-owned)
# =============================================================================

class EUDRSupplyChainLinkBase(BaseModel):
    """Base schema for EUDR supply chain link."""
    from_batch_id: Optional[int] = Field(None, description="Source batch")
    from_operator_id: int = Field(..., description="Source operator")
    to_batch_id: Optional[int] = Field(None, description="Target batch")
    to_operator_id: int = Field(..., description="Target operator")
    link_type: EUDRSupplyChainLinkType
    documentation_reference: Optional[str] = Field(None, max_length=500)


class EUDRSupplyChainLinkCreate(EUDRSupplyChainLinkBase):
    """Schema for creating an EUDR supply chain link."""
    pass


class EUDRSupplyChainLinkResponse(EUDRSupplyChainLinkBase):
    """Schema for EUDR supply chain link response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None

    # Include related data (minimal to avoid cycles)
    from_batch: Optional[EUDRBatchSummary] = None
    to_batch: Optional[EUDRBatchSummary] = None
    from_operator: Optional[EUDROperatorResponse] = None
    to_operator: Optional[EUDROperatorResponse] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# EUDR GEO RISK SNAPSHOT SCHEMAS (Tenant-owned)
# =============================================================================

class EUDRGeoRiskSnapshotBase(BaseModel):
    """Base schema for EUDR geo risk snapshot."""
    supply_site_id: int = Field(..., description="FK to supply site")
    source: EUDRGeoRiskSource
    snapshot_date: Optional[datetime] = None
    deforestation_flag: bool = False
    tree_cover_loss_ha: Optional[float] = Field(None, ge=0)
    protected_area_overlap: bool = False
    risk_score_raw: Optional[float] = Field(None, ge=0, le=100)
    risk_level: Optional[EUDRRiskLevel] = None
    details_json: Optional[Dict[str, Any]] = None


class EUDRGeoRiskSnapshotCreate(EUDRGeoRiskSnapshotBase):
    """Schema for creating an EUDR geo risk snapshot."""
    pass


class EUDRGeoRiskSnapshotResponse(EUDRGeoRiskSnapshotBase):
    """Schema for EUDR geo risk snapshot response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EUDRGeoRiskRefreshRequest(BaseModel):
    """Request schema for refreshing geo risk for a site."""
    source: EUDRGeoRiskSource = EUDRGeoRiskSource.MOCK
    force_refresh: bool = Field(default=False, description="Force refresh even if recent data exists")


class EUDRGeoRiskRefreshResponse(BaseModel):
    """Response schema for geo risk refresh."""
    supply_site_id: int
    snapshot: EUDRGeoRiskSnapshotResponse
    was_cached: bool = False


# =============================================================================
# EUDR DUE DILIGENCE SCHEMAS (Tenant-owned)
# =============================================================================

class EUDRDueDiligenceBase(BaseModel):
    """Base schema for EUDR due diligence."""
    operator_id: int = Field(..., description="FK to operator responsible")
    reference: Optional[str] = Field(None, max_length=100, description="DD statement ID")
    commodity_id: int = Field(..., description="FK to commodity")
    period_start: datetime = Field(..., description="Start of period covered")
    period_end: datetime = Field(..., description="End of period covered")


class EUDRDueDiligenceCreate(EUDRDueDiligenceBase):
    """Schema for creating an EUDR due diligence."""
    batch_ids: Optional[List[int]] = Field(None, description="Batches to include in DD")


class EUDRDueDiligenceUpdate(BaseModel):
    """Schema for updating an EUDR due diligence."""
    reference: Optional[str] = Field(None, max_length=100)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    status: Optional[EUDRDueDiligenceStatus] = None
    justification_summary: Optional[str] = None


class EUDRDueDiligenceResponse(EUDRDueDiligenceBase):
    """Schema for EUDR due diligence response."""
    id: int
    tenant_id: str
    status: EUDRDueDiligenceStatus
    overall_risk_level: Optional[EUDRRiskLevel] = None
    overall_risk_score: Optional[float] = None
    justification_summary: Optional[str] = None
    total_volume: float = 0.0
    total_volume_unit: str = "tonne"
    batch_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = None

    # Include related data
    operator: Optional[EUDROperatorResponse] = None
    commodity: Optional[EUDRCommodityResponse] = None
    batch_links: Optional[List["EUDRDueDiligenceBatchLinkResponse"]] = None

    model_config = ConfigDict(from_attributes=True)


class EUDRDueDiligenceSummary(BaseModel):
    """Summary schema for DD list views."""
    id: int
    tenant_id: str
    reference: Optional[str] = None
    operator_id: int
    commodity_id: int
    period_start: datetime
    period_end: datetime
    status: EUDRDueDiligenceStatus
    overall_risk_level: Optional[EUDRRiskLevel] = None
    overall_risk_score: Optional[float] = None
    batch_count: int = 0
    total_volume: float = 0.0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# EUDR DUE DILIGENCE BATCH LINK SCHEMAS
# =============================================================================

class EUDRDueDiligenceBatchLinkBase(BaseModel):
    """Base schema for DD batch link."""
    batch_id: int = Field(..., description="FK to batch")
    included_volume: Optional[float] = Field(None, ge=0)
    included_volume_unit: str = Field(default="tonne", max_length=20)
    assessment_notes: Optional[str] = None


class EUDRDueDiligenceBatchLinkCreate(EUDRDueDiligenceBatchLinkBase):
    """Schema for creating a DD batch link."""
    pass


class EUDRDueDiligenceBatchLinkResponse(EUDRDueDiligenceBatchLinkBase):
    """Schema for DD batch link response."""
    id: int
    due_diligence_id: int
    batch_risk_score: Optional[float] = None
    batch_risk_level: Optional[EUDRRiskLevel] = None
    created_at: Optional[datetime] = None

    # Include batch details
    batch: Optional[EUDRBatchSummary] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# RISK EVALUATION REQUEST/RESPONSE SCHEMAS
# =============================================================================

class EUDRRiskEvaluateRequest(BaseModel):
    """Request schema for triggering risk evaluation on a DD."""
    due_diligence_id: int
    recalculate_all: bool = Field(
        default=False,
        description="If True, recalculate all batch risks; if False, only calculate missing"
    )


class EUDRBatchRiskResult(BaseModel):
    """Result of a single batch risk calculation."""
    batch_id: int
    batch_reference: str
    risk_score: float
    risk_level: EUDRRiskLevel
    commodity_risk: float = Field(description="Risk from commodity baseline")
    geo_risk: float = Field(description="Risk from geospatial factors")
    supply_chain_risk: float = Field(description="Risk from supply chain complexity")
    documentation_risk: float = Field(description="Risk from missing documentation")


class EUDRRiskEvaluateResponse(BaseModel):
    """Response schema for risk evaluation."""
    due_diligence_id: int
    overall_risk_score: float
    overall_risk_level: EUDRRiskLevel
    batches_evaluated: int
    batches_skipped: int
    batch_results: List[EUDRBatchRiskResult]
    risk_breakdown: Dict[str, float] = Field(
        description="Breakdown: low/medium/high batch counts"
    )
    errors: List[str] = []


# =============================================================================
# AGGREGATION/REPORT SCHEMAS
# =============================================================================

class EUDRSupplyChainSummary(BaseModel):
    """Summary of supply chain complexity for a DD."""
    total_links: int
    average_hops: float
    max_hops: int
    unique_operators: int
    unique_countries: List[str]
    link_type_breakdown: Dict[str, int]


class EUDRGeoRiskSummary(BaseModel):
    """Summary of geospatial risk across sites."""
    total_sites: int
    sites_with_coordinates: int
    sites_with_risk_data: int
    deforestation_flagged_sites: int
    protected_area_overlap_sites: int
    total_tree_cover_loss_ha: float
    risk_level_breakdown: Dict[str, int]


class EUDRDueDiligenceBreakdown(BaseModel):
    """Detailed breakdown of a due diligence assessment."""
    due_diligence_id: int
    overall_risk_level: EUDRRiskLevel
    overall_risk_score: float
    total_volume: float
    total_volume_unit: str
    batch_count: int
    supply_chain_summary: EUDRSupplyChainSummary
    geo_risk_summary: EUDRGeoRiskSummary
    risk_by_batch: List[EUDRBatchRiskResult]
    risk_by_country: Dict[str, float]
    risk_by_commodity: Dict[str, float]


# =============================================================================
# EXPORT SCHEMAS
# =============================================================================

class EUDRExportRequest(BaseModel):
    """Request schema for EUDR report export."""
    due_diligence_id: int
    format: str = Field(default="pdf", description="Export format: pdf, xhtml, csv")
    include_batch_details: bool = True
    include_supply_chain: bool = True
    include_geo_risk: bool = True


class EUDRExportResponse(BaseModel):
    """Response schema for EUDR export."""
    due_diligence_id: int
    format: str
    file_url: Optional[str] = None
    file_content: Optional[str] = None  # Base64 encoded for inline response
    generated_at: datetime


# Forward reference update for circular dependency
EUDRDueDiligenceResponse.model_rebuild()
