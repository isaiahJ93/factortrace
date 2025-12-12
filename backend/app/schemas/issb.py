# app/schemas/issb.py
"""
ISSB (IFRS S1 + S2) Pydantic Schemas.

Provides request/response schemas for ISSB API endpoints.

Reference: docs/regimes/issb.md
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.issb import (
    ISSBConsolidationMethod,
    ISSBMetricType,
    ISSBRiskType,
    ISSBTimeHorizon,
    ISSBFinancialImpactType,
    ISSBLikelihood,
    ISSBEmissionsScope,
    ISSBTargetType,
    ISSBTargetStatus,
    ISSBScenarioResultMetric,
    ISSBMaterialityTopic,
    ISSBDisclosureStandard,
    ISSBDisclosureSection,
    ISSBDisclosureStatus,
)


# =============================================================================
# VALIDATION HELPERS
# =============================================================================

def validate_currency_code(v: str) -> str:
    """Validate ISO 4217 currency code."""
    if len(v) != 3 or not v.isalpha() or not v.isupper():
        raise ValueError("Currency must be 3-letter uppercase ISO 4217 code")
    return v


def validate_score_range(v: Optional[float]) -> Optional[float]:
    """Validate materiality score is 0-100."""
    if v is not None and (v < 0 or v > 100):
        raise ValueError("Score must be between 0 and 100")
    return v


def validate_year(v: int) -> int:
    """Validate year is reasonable."""
    if v < 1900 or v > 2100:
        raise ValueError("Year must be between 1900 and 2100")
    return v


# =============================================================================
# ISSB REPORTING UNIT SCHEMAS
# =============================================================================

class ISSBReportingUnitBase(BaseModel):
    """Base schema for ISSB reporting unit."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    consolidation_method: ISSBConsolidationMethod = ISSBConsolidationMethod.FULL
    parent_unit_id: Optional[int] = None
    sector: Optional[str] = Field(None, max_length=100)
    industry_code: Optional[str] = Field(None, max_length=20, description="NACE/NAICS code")
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return validate_currency_code(v)


class ISSBReportingUnitCreate(ISSBReportingUnitBase):
    """Schema for creating an ISSB reporting unit."""
    pass


class ISSBReportingUnitUpdate(BaseModel):
    """Schema for updating an ISSB reporting unit."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    consolidation_method: Optional[ISSBConsolidationMethod] = None
    parent_unit_id: Optional[int] = None
    sector: Optional[str] = Field(None, max_length=100)
    industry_code: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ISSBReportingUnitResponse(ISSBReportingUnitBase):
    """Schema for ISSB reporting unit response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ISSB FINANCIAL METRIC SCHEMAS
# =============================================================================

class ISSBFinancialMetricBase(BaseModel):
    """Base schema for ISSB financial metric."""
    reporting_unit_id: int
    period_start: datetime
    period_end: datetime
    metric_type: ISSBMetricType
    value: float
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    segment: Optional[str] = Field(None, max_length=100, description="Product line/geography")
    is_audited: bool = False
    source: Optional[str] = Field(None, max_length=200, description="Source document/system")
    notes: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return validate_currency_code(v)


class ISSBFinancialMetricCreate(ISSBFinancialMetricBase):
    """Schema for creating an ISSB financial metric."""
    pass


class ISSBFinancialMetricUpdate(BaseModel):
    """Schema for updating an ISSB financial metric."""
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    metric_type: Optional[ISSBMetricType] = None
    value: Optional[float] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    segment: Optional[str] = Field(None, max_length=100)
    is_audited: Optional[bool] = None
    source: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class ISSBFinancialMetricResponse(ISSBFinancialMetricBase):
    """Schema for ISSB financial metric response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ISSB CLIMATE RISK EXPOSURE SCHEMAS
# =============================================================================

class ISSBClimateRiskExposureBase(BaseModel):
    """Base schema for ISSB climate risk exposure."""
    reporting_unit_id: int
    period_start: datetime
    period_end: datetime
    risk_type: ISSBRiskType
    subtype: Optional[str] = Field(None, max_length=50, description="E.g., acute/chronic or policy/technology")
    description: str = Field(..., min_length=1)
    time_horizon: ISSBTimeHorizon
    financial_impact_type: Optional[ISSBFinancialImpactType] = None
    impact_range_low: Optional[float] = Field(None, description="Low estimate of financial impact")
    impact_range_high: Optional[float] = Field(None, description="High estimate of financial impact")
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    qualitative_likelihood: Optional[ISSBLikelihood] = None
    linked_to_emissions: bool = False
    linked_scope: Optional[ISSBEmissionsScope] = None
    mitigation_strategy: Optional[str] = None
    is_mitigated: bool = False
    is_active: bool = True
    notes: Optional[str] = None


class ISSBClimateRiskExposureCreate(ISSBClimateRiskExposureBase):
    """Schema for creating an ISSB climate risk exposure."""
    pass


class ISSBClimateRiskExposureUpdate(BaseModel):
    """Schema for updating an ISSB climate risk exposure."""
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    risk_type: Optional[ISSBRiskType] = None
    subtype: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    time_horizon: Optional[ISSBTimeHorizon] = None
    financial_impact_type: Optional[ISSBFinancialImpactType] = None
    impact_range_low: Optional[float] = None
    impact_range_high: Optional[float] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    qualitative_likelihood: Optional[ISSBLikelihood] = None
    linked_to_emissions: Optional[bool] = None
    linked_scope: Optional[ISSBEmissionsScope] = None
    mitigation_strategy: Optional[str] = None
    is_mitigated: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ISSBClimateRiskExposureResponse(ISSBClimateRiskExposureBase):
    """Schema for ISSB climate risk exposure response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ISSB TARGET SCHEMAS
# =============================================================================

class ISSBTargetBase(BaseModel):
    """Base schema for ISSB target."""
    reporting_unit_id: int
    name: str = Field(..., min_length=1, max_length=200)
    target_type: ISSBTargetType
    scope: Optional[ISSBEmissionsScope] = None
    base_year: int
    target_year: int
    base_value: float
    target_value: float
    current_value: Optional[float] = Field(None, description="Most recent actual value")
    unit: str = Field(..., max_length=50, description="e.g., tCO2e, tCO2e/revenue, %")
    status: ISSBTargetStatus = ISSBTargetStatus.NOT_STARTED
    progress_percentage: Optional[float] = Field(None, ge=0, le=100, description="0-100%")
    is_sbti_validated: bool = False
    validation_body: Optional[str] = Field(None, max_length=100)
    validation_date: Optional[datetime] = None
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator("base_year", "target_year")
    @classmethod
    def validate_years(cls, v: int) -> int:
        return validate_year(v)


class ISSBTargetCreate(ISSBTargetBase):
    """Schema for creating an ISSB target."""
    pass


class ISSBTargetUpdate(BaseModel):
    """Schema for updating an ISSB target."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    target_type: Optional[ISSBTargetType] = None
    scope: Optional[ISSBEmissionsScope] = None
    base_year: Optional[int] = None
    target_year: Optional[int] = None
    base_value: Optional[float] = None
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)
    status: Optional[ISSBTargetStatus] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    is_sbti_validated: Optional[bool] = None
    validation_body: Optional[str] = Field(None, max_length=100)
    validation_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ISSBTargetResponse(ISSBTargetBase):
    """Schema for ISSB target response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ISSB SCENARIO SCHEMAS
# =============================================================================

class ISSBScenarioBase(BaseModel):
    """Base schema for ISSB scenario."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    temperature_pathway: str = Field(..., max_length=20, description="e.g., '1.5C', '2C', '3C'")
    reference_source: Optional[str] = Field(None, max_length=200, description="e.g., 'NGFS Current Policies'")
    carbon_price_path_json: Optional[Dict[str, float]] = Field(
        None,
        description="Year to carbon price mapping, e.g., {'2025': 60, '2030': 100}"
    )
    policy_assumptions: Optional[str] = None
    market_assumptions: Optional[str] = None
    technology_assumptions: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    is_default: bool = False
    is_active: bool = True
    notes: Optional[str] = None


class ISSBScenarioCreate(ISSBScenarioBase):
    """Schema for creating an ISSB scenario."""
    pass


class ISSBScenarioUpdate(BaseModel):
    """Schema for updating an ISSB scenario."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    temperature_pathway: Optional[str] = Field(None, max_length=20)
    reference_source: Optional[str] = Field(None, max_length=200)
    carbon_price_path_json: Optional[Dict[str, float]] = None
    policy_assumptions: Optional[str] = None
    market_assumptions: Optional[str] = None
    technology_assumptions: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ISSBScenarioResponse(ISSBScenarioBase):
    """Schema for ISSB scenario response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ISSB SCENARIO RESULT SCHEMAS
# =============================================================================

class ISSBScenarioResultBase(BaseModel):
    """Base schema for ISSB scenario result."""
    scenario_id: int
    reporting_unit_id: int
    period_start: datetime
    period_end: datetime
    projection_year: Optional[int] = Field(None, description="Specific year for projection")
    metric_type: ISSBScenarioResultMetric
    base_case_value: Optional[float] = Field(None, description="Value without scenario impact")
    scenario_value: Optional[float] = Field(None, description="Value with scenario impact")
    delta_value: Optional[float] = Field(None, description="Difference (scenario - base)")
    delta_percentage: Optional[float] = Field(None, description="Percentage change")
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    calculation_date: Optional[datetime] = None
    carbon_price_used: Optional[float] = Field(None, description="Carbon price used for calculation")
    emissions_used: Optional[float] = Field(None, description="tCO2e used for calculation")
    notes: Optional[str] = None


class ISSBScenarioResultCreate(ISSBScenarioResultBase):
    """Schema for creating an ISSB scenario result."""
    pass


class ISSBScenarioResultUpdate(BaseModel):
    """Schema for updating an ISSB scenario result."""
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    projection_year: Optional[int] = None
    metric_type: Optional[ISSBScenarioResultMetric] = None
    base_case_value: Optional[float] = None
    scenario_value: Optional[float] = None
    delta_value: Optional[float] = None
    delta_percentage: Optional[float] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    calculation_date: Optional[datetime] = None
    carbon_price_used: Optional[float] = None
    emissions_used: Optional[float] = None
    notes: Optional[str] = None


class ISSBScenarioResultResponse(ISSBScenarioResultBase):
    """Schema for ISSB scenario result response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ISSB MATERIALITY ASSESSMENT SCHEMAS
# =============================================================================

class ISSBMaterialityAssessmentBase(BaseModel):
    """Base schema for ISSB materiality assessment."""
    reporting_unit_id: int
    period_start: datetime
    period_end: datetime
    topic: ISSBMaterialityTopic = ISSBMaterialityTopic.CLIMATE
    impact_materiality_score: Optional[float] = Field(
        None, ge=0, le=100, description="Impact on environment/society (0-100)"
    )
    financial_materiality_score: Optional[float] = Field(
        None, ge=0, le=100, description="Impact on financial performance (0-100)"
    )
    material: Optional[bool] = Field(None, description="Is topic material?")
    materiality_threshold: float = Field(default=50.0, description="Threshold used for determination")
    justification: Optional[str] = None
    methodology_reference: Optional[str] = Field(None, max_length=200, description="e.g., '2D matrix'")
    emissions_total_tco2e: Optional[float] = None
    revenue_total: Optional[float] = None
    revenue_exposed: Optional[float] = Field(None, description="Revenue exposed to climate risk")
    is_final: bool = False
    reviewed_by: Optional[str] = Field(None, max_length=200)
    review_date: Optional[datetime] = None


class ISSBMaterialityAssessmentCreate(ISSBMaterialityAssessmentBase):
    """Schema for creating an ISSB materiality assessment."""
    pass


class ISSBMaterialityAssessmentUpdate(BaseModel):
    """Schema for updating an ISSB materiality assessment."""
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    topic: Optional[ISSBMaterialityTopic] = None
    impact_materiality_score: Optional[float] = Field(None, ge=0, le=100)
    financial_materiality_score: Optional[float] = Field(None, ge=0, le=100)
    material: Optional[bool] = None
    materiality_threshold: Optional[float] = None
    justification: Optional[str] = None
    methodology_reference: Optional[str] = Field(None, max_length=200)
    emissions_total_tco2e: Optional[float] = None
    revenue_total: Optional[float] = None
    revenue_exposed: Optional[float] = None
    is_final: Optional[bool] = None
    reviewed_by: Optional[str] = Field(None, max_length=200)
    review_date: Optional[datetime] = None


class ISSBMaterialityAssessmentResponse(ISSBMaterialityAssessmentBase):
    """Schema for ISSB materiality assessment response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ISSB DISCLOSURE STATEMENT SCHEMAS
# =============================================================================

class ISSBDisclosureStatementBase(BaseModel):
    """Base schema for ISSB disclosure statement."""
    reporting_unit_id: int
    period_start: datetime
    period_end: datetime
    standard: ISSBDisclosureStandard = ISSBDisclosureStandard.IFRS_S2
    section: ISSBDisclosureSection
    headline_summary: Optional[str] = Field(None, max_length=500, description="Short summary for executive view")
    body_markdown: Optional[str] = Field(None, description="Full disclosure in markdown format")
    body_html: Optional[str] = Field(None, description="Rendered HTML version")
    generated_by_system: bool = True
    generation_date: Optional[datetime] = None
    template_version: Optional[str] = Field(None, max_length=20)
    last_edited_by: Optional[str] = Field(None, max_length=200)
    last_edited_at: Optional[datetime] = None
    edit_count: int = 0
    status: ISSBDisclosureStatus = ISSBDisclosureStatus.DRAFT
    approved_by: Optional[str] = Field(None, max_length=200)
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None


class ISSBDisclosureStatementCreate(ISSBDisclosureStatementBase):
    """Schema for creating an ISSB disclosure statement."""
    pass


class ISSBDisclosureStatementUpdate(BaseModel):
    """Schema for updating an ISSB disclosure statement."""
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    standard: Optional[ISSBDisclosureStandard] = None
    section: Optional[ISSBDisclosureSection] = None
    headline_summary: Optional[str] = Field(None, max_length=500)
    body_markdown: Optional[str] = None
    body_html: Optional[str] = None
    generated_by_system: Optional[bool] = None
    generation_date: Optional[datetime] = None
    template_version: Optional[str] = Field(None, max_length=20)
    last_edited_by: Optional[str] = Field(None, max_length=200)
    last_edited_at: Optional[datetime] = None
    edit_count: Optional[int] = None
    status: Optional[ISSBDisclosureStatus] = None
    approved_by: Optional[str] = Field(None, max_length=200)
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None


class ISSBDisclosureStatementResponse(ISSBDisclosureStatementBase):
    """Schema for ISSB disclosure statement response."""
    id: int
    tenant_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# COMPUTED / ANALYSIS SCHEMAS
# =============================================================================

class ISSBMaterialityEvaluationRequest(BaseModel):
    """Request schema for materiality evaluation."""
    reporting_unit_id: int
    period_start: datetime
    period_end: datetime
    topic: ISSBMaterialityTopic = ISSBMaterialityTopic.CLIMATE
    threshold: float = Field(default=50.0, ge=0, le=100)


class ISSBMaterialityEvaluationResponse(BaseModel):
    """Response schema for materiality evaluation."""
    reporting_unit_id: int
    topic: ISSBMaterialityTopic
    impact_materiality_score: float
    financial_materiality_score: float
    overall_material: bool
    threshold_used: float
    justification: str
    assessment_id: Optional[int] = None


class ISSBScenarioAnalysisRequest(BaseModel):
    """Request schema for scenario analysis."""
    reporting_unit_id: int
    scenario_id: int
    projection_year: int
    emissions_tco2e: float = Field(..., gt=0, description="Total emissions in tCO2e")
    base_revenue: Optional[float] = Field(None, description="Base case revenue")
    base_ebitda: Optional[float] = Field(None, description="Base case EBITDA")


class ISSBScenarioAnalysisResponse(BaseModel):
    """Response schema for scenario analysis."""
    scenario_id: int
    scenario_name: str
    temperature_pathway: str
    projection_year: int
    carbon_price: float
    cost_of_carbon: float
    results: List[ISSBScenarioResultResponse]


class ISSBDisclosureGenerateRequest(BaseModel):
    """Request schema for disclosure generation."""
    reporting_unit_id: int
    period_start: datetime
    period_end: datetime
    standard: ISSBDisclosureStandard = ISSBDisclosureStandard.IFRS_S2
    sections: Optional[List[ISSBDisclosureSection]] = Field(
        None,
        description="Sections to generate. If None, generate all."
    )


class ISSBDisclosureGenerateResponse(BaseModel):
    """Response schema for disclosure generation."""
    reporting_unit_id: int
    period_start: datetime
    period_end: datetime
    standard: ISSBDisclosureStandard
    disclosures: List[ISSBDisclosureStatementResponse]
    generation_timestamp: datetime


# =============================================================================
# LIST QUERY PARAMETERS
# =============================================================================

class ISSBReportingUnitListParams(BaseModel):
    """Query parameters for listing reporting units."""
    is_active: Optional[bool] = None
    sector: Optional[str] = None
    parent_unit_id: Optional[int] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class ISSBFinancialMetricListParams(BaseModel):
    """Query parameters for listing financial metrics."""
    reporting_unit_id: Optional[int] = None
    metric_type: Optional[ISSBMetricType] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    is_audited: Optional[bool] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class ISSBClimateRiskListParams(BaseModel):
    """Query parameters for listing climate risk exposures."""
    reporting_unit_id: Optional[int] = None
    risk_type: Optional[ISSBRiskType] = None
    time_horizon: Optional[ISSBTimeHorizon] = None
    is_active: Optional[bool] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class ISSBTargetListParams(BaseModel):
    """Query parameters for listing targets."""
    reporting_unit_id: Optional[int] = None
    target_type: Optional[ISSBTargetType] = None
    status: Optional[ISSBTargetStatus] = None
    target_year: Optional[int] = None
    is_active: Optional[bool] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class ISSBScenarioListParams(BaseModel):
    """Query parameters for listing scenarios."""
    temperature_pathway: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class ISSBMaterialityListParams(BaseModel):
    """Query parameters for listing materiality assessments."""
    reporting_unit_id: Optional[int] = None
    topic: Optional[ISSBMaterialityTopic] = None
    is_final: Optional[bool] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class ISSBDisclosureListParams(BaseModel):
    """Query parameters for listing disclosure statements."""
    reporting_unit_id: Optional[int] = None
    standard: Optional[ISSBDisclosureStandard] = None
    section: Optional[ISSBDisclosureSection] = None
    status: Optional[ISSBDisclosureStatus] = None
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)
