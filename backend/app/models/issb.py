# app/models/issb.py
"""
ISSB (IFRS S1 + S2) Models - Multi-tenant enabled.

Implements ISSB sustainability and climate-related financial disclosures:
- IFRS S1: General sustainability disclosures
- IFRS S2: Climate-related disclosures

Key entities:
- ISSBReportingUnit: Business units/segments for reporting (tenant-owned)
- ISSBFinancialMetric: Financial metrics linked to reporting units (tenant-owned)
- ISSBClimateRiskExposure: Physical and transition risk exposures (tenant-owned)
- ISSBTarget: Emissions and climate targets (tenant-owned)
- ISSBScenario: Climate scenario definitions (tenant-owned)
- ISSBScenarioResult: Results of scenario analysis (tenant-owned)
- ISSBMaterialityAssessment: Double materiality assessments (tenant-owned)
- ISSBDisclosureStatement: Generated disclosure statements (tenant-owned)

Security: All ISSB data queries MUST be filtered by tenant_id.

Reference: docs/regimes/issb.md
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, Index, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


# =============================================================================
# ENUMS
# =============================================================================

class ISSBConsolidationMethod(str, enum.Enum):
    """Consolidation method for reporting units."""
    FULL = "full"
    EQUITY = "equity"
    PROPORTIONATE = "proportionate"


class ISSBMetricType(str, enum.Enum):
    """Types of financial metrics."""
    REVENUE = "revenue"
    EBITDA = "ebitda"
    EBIT = "ebit"
    CAPEX = "capex"
    OPEX = "opex"
    ASSETS = "assets"
    LIABILITIES = "liabilities"
    CARBON_PRICE_EXPOSURE = "carbon_price_exposure"
    NET_INCOME = "net_income"
    FREE_CASH_FLOW = "free_cash_flow"


class ISSBRiskType(str, enum.Enum):
    """Climate risk type classification."""
    PHYSICAL = "physical"
    TRANSITION = "transition"


class ISSBPhysicalRiskSubtype(str, enum.Enum):
    """Physical climate risk subtypes."""
    ACUTE = "acute"  # Extreme weather events
    CHRONIC = "chronic"  # Long-term shifts


class ISSBTransitionRiskSubtype(str, enum.Enum):
    """Transition climate risk subtypes."""
    POLICY = "policy"
    TECHNOLOGY = "technology"
    MARKET = "market"
    REPUTATION = "reputation"
    LEGAL = "legal"


class ISSBTimeHorizon(str, enum.Enum):
    """Time horizon for risk assessment."""
    SHORT = "short"  # 0-2 years
    MEDIUM = "medium"  # 2-5 years
    LONG = "long"  # 5+ years


class ISSBFinancialImpactType(str, enum.Enum):
    """Type of financial impact from climate risk."""
    REVENUE_DOWNSIDE = "revenue_downside"
    REVENUE_UPSIDE = "revenue_upside"
    COST_UPSIDE = "cost_upside"  # Increased costs
    COST_DOWNSIDE = "cost_downside"  # Reduced costs
    ASSET_IMPAIRMENT = "asset_impairment"
    STRANDED_ASSETS = "stranded_assets"
    CAPEX_REQUIREMENT = "capex_requirement"
    INSURANCE_COST = "insurance_cost"


class ISSBLikelihood(str, enum.Enum):
    """Qualitative likelihood assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ISSBEmissionsScope(str, enum.Enum):
    """Emissions scope classification."""
    SCOPE1 = "scope1"
    SCOPE2 = "scope2"
    SCOPE3 = "scope3"
    COMBINED = "combined"
    MIXED = "mixed"


class ISSBTargetType(str, enum.Enum):
    """Types of climate targets."""
    ABSOLUTE_EMISSIONS = "absolute_emissions"
    EMISSIONS_INTENSITY = "emissions_intensity"
    RENEWABLES_SHARE = "renewables_share"
    CAPEX_ALIGNMENT = "capex_alignment"
    NET_ZERO = "net_zero"
    SCIENCE_BASED = "science_based"


class ISSBTargetStatus(str, enum.Enum):
    """Status of target progress."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    OFF_TRACK = "off_track"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"


class ISSBScenarioResultMetric(str, enum.Enum):
    """Metrics computed in scenario analysis."""
    REVENUE = "revenue"
    EBITDA = "ebitda"
    COST_OF_CARBON = "cost_of_carbon"
    CAPEX_REQUIRED = "capex_required"
    STRANDED_ASSETS = "stranded_assets"
    MARGIN_IMPACT = "margin_impact"
    REVENUE_AT_RISK = "revenue_at_risk"


class ISSBMaterialityTopic(str, enum.Enum):
    """Topics for materiality assessment."""
    CLIMATE = "climate"
    WATER = "water"
    BIODIVERSITY = "biodiversity"
    CIRCULAR_ECONOMY = "circular_economy"
    POLLUTION = "pollution"
    WORKFORCE = "workforce"


class ISSBDisclosureStandard(str, enum.Enum):
    """ISSB disclosure standard."""
    IFRS_S1 = "IFRS_S1"  # General sustainability
    IFRS_S2 = "IFRS_S2"  # Climate-related


class ISSBDisclosureSection(str, enum.Enum):
    """ISSB disclosure sections per IFRS S2."""
    GOVERNANCE = "governance"
    STRATEGY = "strategy"
    RISK_MANAGEMENT = "risk_management"
    METRICS_TARGETS = "metrics_targets"


class ISSBDisclosureStatus(str, enum.Enum):
    """Status of disclosure statement."""
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"


# =============================================================================
# ISSB REPORTING UNIT (Tenant-owned)
# =============================================================================

class ISSBReportingUnit(Base):
    """
    Business unit/segment for ISSB reporting.

    Security: This is TENANT-OWNED data. All queries MUST filter by tenant_id.

    Examples: "Group", "EU Operations", "Manufacturing Segment", "Retail Division"
    """
    __tablename__ = "issb_reporting_units"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Unit identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Financial reporting
    currency = Column(
        String(3),
        nullable=False,
        default="EUR",
        comment="ISO 4217 currency code"
    )
    consolidation_method = Column(
        SQLEnum(ISSBConsolidationMethod),
        default=ISSBConsolidationMethod.FULL,
        nullable=False
    )

    # Hierarchy (optional)
    parent_unit_id = Column(
        Integer,
        ForeignKey("issb_reporting_units.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Sector/industry classification
    sector = Column(String(100), nullable=True)
    industry_code = Column(String(20), nullable=True, comment="NACE/NAICS code")

    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="issb_reporting_units")
    parent_unit = relationship("ISSBReportingUnit", remote_side=[id])
    financial_metrics = relationship("ISSBFinancialMetric", back_populates="reporting_unit", cascade="all, delete-orphan")
    climate_risk_exposures = relationship("ISSBClimateRiskExposure", back_populates="reporting_unit", cascade="all, delete-orphan")
    targets = relationship("ISSBTarget", back_populates="reporting_unit", cascade="all, delete-orphan")
    scenario_results = relationship("ISSBScenarioResult", back_populates="reporting_unit", cascade="all, delete-orphan")
    materiality_assessments = relationship("ISSBMaterialityAssessment", back_populates="reporting_unit", cascade="all, delete-orphan")
    disclosure_statements = relationship("ISSBDisclosureStatement", back_populates="reporting_unit", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_issb_unit_tenant_name', 'tenant_id', 'name'),
        Index('idx_issb_unit_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_issb_unit_tenant_parent', 'tenant_id', 'parent_unit_id'),
    )

    def __repr__(self):
        return f"<ISSBReportingUnit(id={self.id}, name={self.name})>"


# =============================================================================
# ISSB FINANCIAL METRIC (Tenant-owned via Reporting Unit)
# =============================================================================

class ISSBFinancialMetric(Base):
    """
    Financial metric linked to a reporting unit and period.

    Security: Tenant isolation through parent reporting_unit.

    Supports metrics like revenue, EBITDA, CAPEX, etc. for scenario analysis
    and financial materiality assessment.
    """
    __tablename__ = "issb_financial_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Link to reporting unit
    reporting_unit_id = Column(
        Integer,
        ForeignKey("issb_reporting_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Metric details
    metric_type = Column(
        SQLEnum(ISSBMetricType),
        nullable=False,
        index=True
    )
    value = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")

    # Optional segment breakdown
    segment = Column(String(100), nullable=True, comment="Product line/geography")

    # Verification
    is_audited = Column(Boolean, default=False)
    source = Column(String(200), nullable=True, comment="Source document/system")

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    reporting_unit = relationship("ISSBReportingUnit", back_populates="financial_metrics")

    __table_args__ = (
        Index('idx_issb_metric_tenant_unit', 'tenant_id', 'reporting_unit_id'),
        Index('idx_issb_metric_tenant_type', 'tenant_id', 'metric_type'),
        Index('idx_issb_metric_tenant_period', 'tenant_id', 'period_start', 'period_end'),
        Index('idx_issb_metric_unit_type_period', 'reporting_unit_id', 'metric_type', 'period_start'),
    )

    def __repr__(self):
        return f"<ISSBFinancialMetric(id={self.id}, type={self.metric_type.value}, value={self.value})>"


# =============================================================================
# ISSB CLIMATE RISK EXPOSURE (Tenant-owned)
# =============================================================================

class ISSBClimateRiskExposure(Base):
    """
    Climate risk exposure assessment for ISSB reporting.

    Security: This is TENANT-OWNED data. All queries MUST filter by tenant_id.

    Captures both physical and transition risks per IFRS S2 requirements.
    """
    __tablename__ = "issb_climate_risk_exposures"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Link to reporting unit
    reporting_unit_id = Column(
        Integer,
        ForeignKey("issb_reporting_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Risk classification
    risk_type = Column(
        SQLEnum(ISSBRiskType),
        nullable=False,
        index=True,
        comment="Physical or Transition risk"
    )
    subtype = Column(
        String(50),
        nullable=True,
        comment="E.g., acute/chronic for physical; policy/technology/market for transition"
    )
    description = Column(Text, nullable=False)

    # Time horizon
    time_horizon = Column(
        SQLEnum(ISSBTimeHorizon),
        nullable=False,
        index=True
    )

    # Financial impact
    financial_impact_type = Column(
        SQLEnum(ISSBFinancialImpactType),
        nullable=True
    )
    impact_range_low = Column(Float, nullable=True, comment="Low estimate of financial impact")
    impact_range_high = Column(Float, nullable=True, comment="High estimate of financial impact")
    currency = Column(String(3), nullable=True, default="EUR")

    # Likelihood assessment
    qualitative_likelihood = Column(
        SQLEnum(ISSBLikelihood),
        nullable=True
    )

    # Emissions linkage
    linked_to_emissions = Column(Boolean, default=False)
    linked_scope = Column(
        SQLEnum(ISSBEmissionsScope),
        nullable=True,
        comment="Which emissions scope this risk relates to"
    )

    # Mitigation status
    mitigation_strategy = Column(Text, nullable=True)
    is_mitigated = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    reporting_unit = relationship("ISSBReportingUnit", back_populates="climate_risk_exposures")

    __table_args__ = (
        Index('idx_issb_risk_tenant_unit', 'tenant_id', 'reporting_unit_id'),
        Index('idx_issb_risk_tenant_type', 'tenant_id', 'risk_type'),
        Index('idx_issb_risk_tenant_horizon', 'tenant_id', 'time_horizon'),
        Index('idx_issb_risk_unit_type_horizon', 'reporting_unit_id', 'risk_type', 'time_horizon'),
    )

    def __repr__(self):
        return f"<ISSBClimateRiskExposure(id={self.id}, type={self.risk_type.value}, horizon={self.time_horizon.value})>"


# =============================================================================
# ISSB TARGET (Tenant-owned)
# =============================================================================

class ISSBTarget(Base):
    """
    Climate and emissions targets for ISSB reporting.

    Security: Tenant isolation through parent reporting_unit.

    Supports various target types: absolute emissions, intensity, renewables, etc.
    """
    __tablename__ = "issb_targets"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Link to reporting unit
    reporting_unit_id = Column(
        Integer,
        ForeignKey("issb_reporting_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Target definition
    name = Column(String(200), nullable=False)
    target_type = Column(
        SQLEnum(ISSBTargetType),
        nullable=False,
        index=True
    )
    scope = Column(
        SQLEnum(ISSBEmissionsScope),
        nullable=True,
        comment="Emissions scope if applicable"
    )

    # Timeline
    base_year = Column(Integer, nullable=False)
    target_year = Column(Integer, nullable=False, index=True)

    # Values
    base_value = Column(Float, nullable=False)
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=True, comment="Most recent actual value")
    unit = Column(String(50), nullable=False, comment="e.g., tCO2e, tCO2e/revenue, %")

    # Progress tracking
    status = Column(
        SQLEnum(ISSBTargetStatus),
        default=ISSBTargetStatus.NOT_STARTED,
        nullable=False,
        index=True
    )
    progress_percentage = Column(Float, nullable=True, comment="0-100%")

    # External validation
    is_sbti_validated = Column(Boolean, default=False, comment="Science Based Targets initiative validated")
    validation_body = Column(String(100), nullable=True)
    validation_date = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    reporting_unit = relationship("ISSBReportingUnit", back_populates="targets")

    __table_args__ = (
        Index('idx_issb_target_tenant_unit', 'tenant_id', 'reporting_unit_id'),
        Index('idx_issb_target_tenant_type', 'tenant_id', 'target_type'),
        Index('idx_issb_target_tenant_status', 'tenant_id', 'status'),
        Index('idx_issb_target_unit_year', 'reporting_unit_id', 'target_year'),
    )

    def __repr__(self):
        return f"<ISSBTarget(id={self.id}, type={self.target_type.value}, year={self.target_year})>"


# =============================================================================
# ISSB SCENARIO (Tenant-owned)
# =============================================================================

class ISSBScenario(Base):
    """
    Climate scenario definition for ISSB scenario analysis.

    Security: This is TENANT-OWNED data. All queries MUST filter by tenant_id.

    Supports scenarios like 1.5°C, 2°C, 3°C pathways with carbon price curves.
    """
    __tablename__ = "issb_scenarios"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Scenario identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Temperature pathway
    temperature_pathway = Column(
        String(20),
        nullable=False,
        comment="e.g., '1.5C', '2C', '3C'"
    )
    reference_source = Column(
        String(200),
        nullable=True,
        comment="e.g., 'NGFS Current Policies', 'IEA Net Zero 2050'"
    )

    # Carbon price path (JSON: year -> price in EUR/tCO2)
    carbon_price_path_json = Column(
        JSON,
        nullable=True,
        comment="Year to carbon price mapping, e.g., {2025: 60, 2030: 100}"
    )

    # Assumptions
    policy_assumptions = Column(Text, nullable=True)
    market_assumptions = Column(Text, nullable=True)
    technology_assumptions = Column(Text, nullable=True)

    # Timeframe
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)

    # Status
    is_default = Column(Boolean, default=False, comment="Default scenario for tenant")
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="issb_scenarios")
    scenario_results = relationship("ISSBScenarioResult", back_populates="scenario", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_issb_scenario_tenant_name', 'tenant_id', 'name'),
        Index('idx_issb_scenario_tenant_temp', 'tenant_id', 'temperature_pathway'),
        Index('idx_issb_scenario_tenant_default', 'tenant_id', 'is_default'),
    )

    def __repr__(self):
        return f"<ISSBScenario(id={self.id}, name={self.name}, pathway={self.temperature_pathway})>"


# =============================================================================
# ISSB SCENARIO RESULT (Tenant-owned)
# =============================================================================

class ISSBScenarioResult(Base):
    """
    Results of climate scenario analysis.

    Security: Tenant isolation through scenario/reporting_unit.

    Stores computed impacts like carbon costs, EBITDA delta, revenue at risk.
    """
    __tablename__ = "issb_scenario_results"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Links
    scenario_id = Column(
        Integer,
        ForeignKey("issb_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reporting_unit_id = Column(
        Integer,
        ForeignKey("issb_reporting_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    projection_year = Column(Integer, nullable=True, comment="Specific year for projection")

    # Result metric
    metric_type = Column(
        SQLEnum(ISSBScenarioResultMetric),
        nullable=False,
        index=True
    )

    # Values
    base_case_value = Column(Float, nullable=True, comment="Value without scenario impact")
    scenario_value = Column(Float, nullable=True, comment="Value with scenario impact")
    delta_value = Column(Float, nullable=True, comment="Difference (scenario - base)")
    delta_percentage = Column(Float, nullable=True, comment="Percentage change")
    currency = Column(String(3), nullable=True, default="EUR")

    # Calculation metadata
    calculation_date = Column(DateTime(timezone=True), nullable=True)
    carbon_price_used = Column(Float, nullable=True, comment="Carbon price used for calculation")
    emissions_used = Column(Float, nullable=True, comment="tCO2e used for calculation")

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant")
    scenario = relationship("ISSBScenario", back_populates="scenario_results")
    reporting_unit = relationship("ISSBReportingUnit", back_populates="scenario_results")

    __table_args__ = (
        Index('idx_issb_result_tenant_scenario', 'tenant_id', 'scenario_id'),
        Index('idx_issb_result_tenant_unit', 'tenant_id', 'reporting_unit_id'),
        Index('idx_issb_result_scenario_unit_metric', 'scenario_id', 'reporting_unit_id', 'metric_type'),
        Index('idx_issb_result_tenant_year', 'tenant_id', 'projection_year'),
    )

    def __repr__(self):
        return f"<ISSBScenarioResult(id={self.id}, metric={self.metric_type.value}, delta={self.delta_value})>"


# =============================================================================
# ISSB MATERIALITY ASSESSMENT (Tenant-owned)
# =============================================================================

class ISSBMaterialityAssessment(Base):
    """
    Double materiality assessment for ISSB reporting.

    Security: Tenant isolation through reporting_unit.

    Assesses both financial materiality and impact materiality per ISSB/CSRD.
    """
    __tablename__ = "issb_materiality_assessments"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Link to reporting unit
    reporting_unit_id = Column(
        Integer,
        ForeignKey("issb_reporting_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Topic being assessed
    topic = Column(
        SQLEnum(ISSBMaterialityTopic),
        nullable=False,
        default=ISSBMaterialityTopic.CLIMATE,
        index=True
    )

    # Materiality scores (0-100)
    impact_materiality_score = Column(
        Float,
        nullable=True,
        comment="Impact on environment/society (0-100)"
    )
    financial_materiality_score = Column(
        Float,
        nullable=True,
        comment="Impact on financial performance (0-100)"
    )

    # Assessment result
    material = Column(Boolean, nullable=True, comment="Is topic material?")
    materiality_threshold = Column(Float, default=50.0, comment="Threshold used for determination")

    # Justification
    justification = Column(Text, nullable=True)
    methodology_reference = Column(String(200), nullable=True, comment="e.g., '2D matrix', 'multi-criteria'")

    # Input data used (for audit trail)
    emissions_total_tco2e = Column(Float, nullable=True)
    revenue_total = Column(Float, nullable=True)
    revenue_exposed = Column(Float, nullable=True, comment="Revenue exposed to climate risk")

    # Status
    is_final = Column(Boolean, default=False)
    reviewed_by = Column(String(200), nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant")
    reporting_unit = relationship("ISSBReportingUnit", back_populates="materiality_assessments")

    __table_args__ = (
        Index('idx_issb_materiality_tenant_unit', 'tenant_id', 'reporting_unit_id'),
        Index('idx_issb_materiality_tenant_topic', 'tenant_id', 'topic'),
        Index('idx_issb_materiality_unit_period', 'reporting_unit_id', 'period_start', 'period_end'),
    )

    def __repr__(self):
        return f"<ISSBMaterialityAssessment(id={self.id}, topic={self.topic.value}, material={self.material})>"


# =============================================================================
# ISSB DISCLOSURE STATEMENT (Tenant-owned)
# =============================================================================

class ISSBDisclosureStatement(Base):
    """
    ISSB disclosure statement for inclusion in annual/sustainability reports.

    Security: This is TENANT-OWNED data. All queries MUST filter by tenant_id.

    Covers IFRS S1 and S2 disclosure sections: Governance, Strategy,
    Risk Management, Metrics & Targets.
    """
    __tablename__ = "issb_disclosure_statements"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Link to reporting unit
    reporting_unit_id = Column(
        Integer,
        ForeignKey("issb_reporting_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Disclosure classification
    standard = Column(
        SQLEnum(ISSBDisclosureStandard),
        nullable=False,
        default=ISSBDisclosureStandard.IFRS_S2,
        index=True
    )
    section = Column(
        SQLEnum(ISSBDisclosureSection),
        nullable=False,
        index=True
    )

    # Content
    headline_summary = Column(String(500), nullable=True, comment="Short summary for executive view")
    body_markdown = Column(Text, nullable=True, comment="Full disclosure in markdown format")
    body_html = Column(Text, nullable=True, comment="Rendered HTML version")

    # Generation metadata
    generated_by_system = Column(Boolean, default=True)
    generation_date = Column(DateTime(timezone=True), nullable=True)
    template_version = Column(String(20), nullable=True)

    # Edit tracking
    last_edited_by = Column(String(200), nullable=True)
    last_edited_at = Column(DateTime(timezone=True), nullable=True)
    edit_count = Column(Integer, default=0)

    # Status
    status = Column(
        SQLEnum(ISSBDisclosureStatus),
        default=ISSBDisclosureStatus.DRAFT,
        nullable=False,
        index=True
    )
    approved_by = Column(String(200), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="issb_disclosure_statements")
    reporting_unit = relationship("ISSBReportingUnit", back_populates="disclosure_statements")

    __table_args__ = (
        Index('idx_issb_disclosure_tenant_unit', 'tenant_id', 'reporting_unit_id'),
        Index('idx_issb_disclosure_tenant_standard', 'tenant_id', 'standard'),
        Index('idx_issb_disclosure_tenant_section', 'tenant_id', 'section'),
        Index('idx_issb_disclosure_tenant_status', 'tenant_id', 'status'),
        Index('idx_issb_disclosure_unit_period', 'reporting_unit_id', 'period_start', 'period_end'),
        Index('idx_issb_disclosure_unit_section', 'reporting_unit_id', 'section', 'standard'),
    )

    def __repr__(self):
        return f"<ISSBDisclosureStatement(id={self.id}, standard={self.standard.value}, section={self.section.value})>"
