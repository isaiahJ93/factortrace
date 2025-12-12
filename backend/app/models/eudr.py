# app/models/eudr.py
"""
EUDR (EU Deforestation Regulation) Models - Multi-tenant enabled.

Implements the EU Deforestation Regulation (EU) 2023/1115 for tracking
commodities, supply chains, geospatial risk, and due diligence.

Key entities:
- EUDRCommodity: Reference data for EUDR-covered commodities (GLOBAL)
- EUDROperator: Operators/traders in the supply chain (tenant-owned)
- EUDRSupplySite: Geographic production sites with coordinates (tenant-owned)
- EUDRBatch: Commodity batches/lots (tenant-owned)
- EUDRSupplyChainLink: Graph edges linking batches through supply chain (tenant-owned)
- EUDRGeoRiskSnapshot: Point-in-time geospatial risk assessments (tenant-owned)
- EUDRDueDiligence: Due diligence statements (tenant-owned)
- EUDRDueDiligenceBatchLink: Links batches to DD statements (tenant-owned)

Security: All tenant-owned EUDR data queries MUST be filtered by tenant_id.

Reference: docs/regimes/eudr.md
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

class EUDRCommodityType(str, enum.Enum):
    """
    EUDR-covered commodities per Regulation (EU) 2023/1115.
    These are the seven core commodity categories.
    """
    CATTLE = "cattle"  # Including beef and leather
    COCOA = "cocoa"
    COFFEE = "coffee"
    PALM_OIL = "palm_oil"
    SOY = "soy"
    TIMBER = "timber"  # Including wood products
    RUBBER = "rubber"


class EUDROperatorRole(str, enum.Enum):
    """Role of an operator in the EUDR supply chain."""
    OPERATOR = "operator"  # EU entity placing goods on market
    TRADER = "trader"  # Making goods available on EU market
    SUPPLIER = "supplier"  # Non-EU supplier/producer


class EUDRSupplyChainLinkType(str, enum.Enum):
    """Type of connection between batches in supply chain."""
    PURCHASE = "purchase"
    PROCESSING = "processing"
    MIXING = "mixing"
    TRANSPORT = "transport"
    AGGREGATION = "aggregation"


class EUDRRiskLevel(str, enum.Enum):
    """Risk level classification for EUDR assessments."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EUDRDueDiligenceStatus(str, enum.Enum):
    """Status of an EUDR due diligence statement."""
    DRAFT = "draft"
    FINAL = "final"
    ARCHIVED = "archived"


class EUDRGeoRiskSource(str, enum.Enum):
    """Source of geospatial risk data."""
    GFW = "GFW"  # Global Forest Watch
    NATIONAL_CADASTRE = "NATIONAL_CADASTRE"
    EUDR_BENCHMARK = "EUDR_BENCHMARK"  # EU benchmarking system
    MANUAL = "MANUAL"  # User-provided assessment
    MOCK = "MOCK"  # For testing/development


# =============================================================================
# EUDR COMMODITY (Reference Data - Not tenant-owned)
# =============================================================================

class EUDRCommodity(Base):
    """
    Reference table for EUDR-covered commodities.

    This is SHARED reference data (not tenant-owned).
    Covers the 7 EUDR commodity categories and their derived products.
    """
    __tablename__ = "eudr_commodities"

    id = Column(Integer, primary_key=True, index=True)

    # Commodity identification
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Commodity name (e.g., 'coffee', 'cocoa', 'palm_oil')"
    )
    commodity_type = Column(
        SQLEnum(EUDRCommodityType),
        nullable=False,
        index=True,
        comment="EUDR commodity category"
    )
    description = Column(String(500), nullable=True)

    # Trade classification
    hs_code = Column(
        String(10),
        nullable=True,
        index=True,
        comment="Harmonized System code (6-10 digits)"
    )

    # Risk profile
    risk_profile_default = Column(
        SQLEnum(EUDRRiskLevel),
        default=EUDRRiskLevel.MEDIUM,
        nullable=False,
        comment="Default risk level for this commodity"
    )

    # Metadata
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    supply_sites = relationship("EUDRSupplySite", back_populates="commodity")
    batches = relationship("EUDRBatch", back_populates="commodity")
    due_diligences = relationship("EUDRDueDiligence", back_populates="commodity")

    __table_args__ = (
        Index('idx_eudr_commodity_type_active', 'commodity_type', 'is_active'),
    )

    def __repr__(self):
        return f"<EUDRCommodity(name={self.name}, type={self.commodity_type.value})>"


# =============================================================================
# EUDR OPERATOR (Tenant-owned)
# =============================================================================

class EUDROperator(Base):
    """
    EUDR operator/trader in the supply chain.

    Security: This is TENANT-OWNED data. All queries MUST filter by tenant_id.

    Represents EU operators, traders, or their suppliers involved in
    EUDR-covered commodity supply chains.
    """
    __tablename__ = "eudr_operators"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Operator identification
    name = Column(String(200), nullable=False)
    role = Column(
        SQLEnum(EUDROperatorRole),
        nullable=False,
        index=True,
        comment="Role in supply chain (operator/trader/supplier)"
    )

    # Location and registration
    country = Column(
        String(2),
        nullable=False,
        index=True,
        comment="ISO 2-letter country code"
    )
    identifier = Column(
        String(100),
        nullable=True,
        comment="VAT number, registration ID, or other identifier"
    )

    # Contact/additional info
    address = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="eudr_operators")
    supply_sites = relationship("EUDRSupplySite", back_populates="operator")
    due_diligences = relationship("EUDRDueDiligence", back_populates="operator")
    # Supply chain links where this operator is source or target
    outgoing_links = relationship(
        "EUDRSupplyChainLink",
        foreign_keys="EUDRSupplyChainLink.from_operator_id",
        back_populates="from_operator"
    )
    incoming_links = relationship(
        "EUDRSupplyChainLink",
        foreign_keys="EUDRSupplyChainLink.to_operator_id",
        back_populates="to_operator"
    )

    __table_args__ = (
        Index('idx_eudr_operator_tenant_role', 'tenant_id', 'role'),
        Index('idx_eudr_operator_tenant_country', 'tenant_id', 'country'),
        Index('idx_eudr_operator_tenant_name', 'tenant_id', 'name'),
    )

    def __repr__(self):
        return f"<EUDROperator(id={self.id}, name={self.name}, role={self.role.value})>"


# =============================================================================
# EUDR SUPPLY SITE (Tenant-owned)
# =============================================================================

class EUDRSupplySite(Base):
    """
    Geographic production/supply site for EUDR commodities.

    Security: This is TENANT-OWNED via operator. All queries MUST filter by tenant_id.

    Represents physical locations (farms, plantations, forests) where
    EUDR commodities are produced. Includes geospatial data for risk assessment.
    """
    __tablename__ = "eudr_supply_sites"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Operator controlling this site
    operator_id = Column(
        Integer,
        ForeignKey("eudr_operators.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Commodity produced at this site
    commodity_id = Column(
        Integer,
        ForeignKey("eudr_commodities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Site identification
    name = Column(String(200), nullable=False)
    site_reference = Column(
        String(100),
        nullable=True,
        comment="External site identifier/reference"
    )

    # Location - country level
    country = Column(
        String(2),
        nullable=False,
        index=True,
        comment="ISO 2-letter country code"
    )
    region = Column(String(100), nullable=True, comment="State/province/region")

    # Geospatial coordinates - centroid (required for risk assessment)
    latitude = Column(
        Float,
        nullable=True,
        comment="Centroid latitude (WGS84)"
    )
    longitude = Column(
        Float,
        nullable=True,
        comment="Centroid longitude (WGS84)"
    )

    # Geospatial polygon (optional, for precise boundary)
    # Stored as GeoJSON text for SQLite compatibility
    # Can be migrated to PostGIS geometry column later
    geometry_geojson = Column(
        Text,
        nullable=True,
        comment="Site boundary as GeoJSON polygon (optional)"
    )

    # Site attributes
    area_ha = Column(
        Float,
        nullable=True,
        comment="Site area in hectares"
    )
    legal_title_reference = Column(
        String(200),
        nullable=True,
        comment="Deed/registry reference for legal title"
    )

    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="eudr_supply_sites")
    operator = relationship("EUDROperator", back_populates="supply_sites")
    commodity = relationship("EUDRCommodity", back_populates="supply_sites")
    batches = relationship("EUDRBatch", back_populates="origin_site")
    georisk_snapshots = relationship(
        "EUDRGeoRiskSnapshot",
        back_populates="supply_site",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_eudr_site_tenant_operator', 'tenant_id', 'operator_id'),
        Index('idx_eudr_site_tenant_commodity', 'tenant_id', 'commodity_id'),
        Index('idx_eudr_site_tenant_country', 'tenant_id', 'country'),
        Index('idx_eudr_site_coordinates', 'latitude', 'longitude'),
    )

    def __repr__(self):
        return f"<EUDRSupplySite(id={self.id}, name={self.name}, country={self.country})>"

    @property
    def has_coordinates(self) -> bool:
        """Check if site has geolocation data."""
        return self.latitude is not None and self.longitude is not None

    @property
    def has_polygon(self) -> bool:
        """Check if site has polygon boundary."""
        return self.geometry_geojson is not None


# =============================================================================
# EUDR BATCH (Tenant-owned)
# =============================================================================

class EUDRBatch(Base):
    """
    Commodity batch/lot for EUDR traceability.

    Security: This is TENANT-OWNED data. All queries MUST filter by tenant_id.

    Represents a specific lot of commodities that can be traced through
    the supply chain from origin to EU market.
    """
    __tablename__ = "eudr_batches"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Batch identification
    batch_reference = Column(
        String(100),
        nullable=False,
        index=True,
        comment="User-provided batch/lot identifier"
    )

    # Commodity
    commodity_id = Column(
        Integer,
        ForeignKey("eudr_commodities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Volume/quantity
    volume = Column(
        Float,
        nullable=False,
        comment="Quantity of commodity"
    )
    volume_unit = Column(
        String(20),
        nullable=False,
        default="tonne",
        comment="Unit of measurement (tonne, kg, m3, bags)"
    )

    # Harvest/production info
    harvest_year = Column(
        Integer,
        nullable=True,
        index=True,
        comment="Year of harvest/production"
    )

    # Origin
    origin_site_id = Column(
        Integer,
        ForeignKey("eudr_supply_sites.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK to origin supply site (if known)"
    )
    origin_country = Column(
        String(2),
        nullable=False,
        index=True,
        comment="Country of origin (ISO 2-letter)"
    )

    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="eudr_batches")
    commodity = relationship("EUDRCommodity", back_populates="batches")
    origin_site = relationship("EUDRSupplySite", back_populates="batches")
    # Supply chain links
    outgoing_links = relationship(
        "EUDRSupplyChainLink",
        foreign_keys="EUDRSupplyChainLink.from_batch_id",
        back_populates="from_batch"
    )
    incoming_links = relationship(
        "EUDRSupplyChainLink",
        foreign_keys="EUDRSupplyChainLink.to_batch_id",
        back_populates="to_batch"
    )
    # Due diligence batch links
    due_diligence_links = relationship(
        "EUDRDueDiligenceBatchLink",
        back_populates="batch",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_eudr_batch_tenant_ref', 'tenant_id', 'batch_reference'),
        Index('idx_eudr_batch_tenant_commodity', 'tenant_id', 'commodity_id'),
        Index('idx_eudr_batch_tenant_origin', 'tenant_id', 'origin_country'),
        Index('idx_eudr_batch_tenant_year', 'tenant_id', 'harvest_year'),
    )

    def __repr__(self):
        return f"<EUDRBatch(id={self.id}, ref={self.batch_reference}, volume={self.volume} {self.volume_unit})>"


# =============================================================================
# EUDR SUPPLY CHAIN LINK (Tenant-owned)
# =============================================================================

class EUDRSupplyChainLink(Base):
    """
    Directed edge in the EUDR supply chain graph.

    Security: This is TENANT-OWNED data. All queries MUST filter by tenant_id.

    Links batches and operators through the supply chain, forming a directed
    graph from origin sites to EU market placement.
    """
    __tablename__ = "eudr_supply_chain_links"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Source (upstream)
    from_batch_id = Column(
        Integer,
        ForeignKey("eudr_batches.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Source batch (nullable if operator-to-operator only)"
    )
    from_operator_id = Column(
        Integer,
        ForeignKey("eudr_operators.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source operator"
    )

    # Target (downstream)
    to_batch_id = Column(
        Integer,
        ForeignKey("eudr_batches.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Target batch (nullable if creates new batch)"
    )
    to_operator_id = Column(
        Integer,
        ForeignKey("eudr_operators.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Target operator"
    )

    # Link characteristics
    link_type = Column(
        SQLEnum(EUDRSupplyChainLinkType),
        nullable=False,
        index=True,
        comment="Type of supply chain connection"
    )

    # Documentation
    documentation_reference = Column(
        String(500),
        nullable=True,
        comment="Reference to invoice, contract, or other documentation"
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="eudr_supply_chain_links")
    from_batch = relationship(
        "EUDRBatch",
        foreign_keys=[from_batch_id],
        back_populates="outgoing_links"
    )
    to_batch = relationship(
        "EUDRBatch",
        foreign_keys=[to_batch_id],
        back_populates="incoming_links"
    )
    from_operator = relationship(
        "EUDROperator",
        foreign_keys=[from_operator_id],
        back_populates="outgoing_links"
    )
    to_operator = relationship(
        "EUDROperator",
        foreign_keys=[to_operator_id],
        back_populates="incoming_links"
    )

    __table_args__ = (
        Index('idx_eudr_link_tenant_from', 'tenant_id', 'from_batch_id', 'from_operator_id'),
        Index('idx_eudr_link_tenant_to', 'tenant_id', 'to_batch_id', 'to_operator_id'),
        Index('idx_eudr_link_tenant_type', 'tenant_id', 'link_type'),
    )

    def __repr__(self):
        return f"<EUDRSupplyChainLink(id={self.id}, type={self.link_type.value})>"


# =============================================================================
# EUDR GEO RISK SNAPSHOT (Tenant-owned)
# =============================================================================

class EUDRGeoRiskSnapshot(Base):
    """
    Point-in-time geospatial risk assessment for a supply site.

    Security: This is TENANT-OWNED via supply site. All queries MUST filter by tenant_id.

    Captures deforestation risk signals, protected area overlaps, and
    other geospatial risk factors at a specific point in time.
    """
    __tablename__ = "eudr_georisk_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Supply site being assessed
    supply_site_id = Column(
        Integer,
        ForeignKey("eudr_supply_sites.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Data source
    source = Column(
        SQLEnum(EUDRGeoRiskSource),
        nullable=False,
        index=True,
        comment="Source of geospatial risk data"
    )
    snapshot_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        index=True,
        comment="Date/time of this risk assessment"
    )

    # Risk signals
    deforestation_flag = Column(
        Boolean,
        default=False,
        comment="Deforestation detected in area"
    )
    tree_cover_loss_ha = Column(
        Float,
        nullable=True,
        comment="Tree cover loss in hectares (since cutoff date)"
    )
    protected_area_overlap = Column(
        Boolean,
        default=False,
        comment="Site overlaps with protected area"
    )

    # Computed risk score
    risk_score_raw = Column(
        Float,
        nullable=True,
        comment="Raw risk score (0-100)"
    )
    risk_level = Column(
        SQLEnum(EUDRRiskLevel),
        nullable=True,
        index=True,
        comment="Computed risk level (low/medium/high)"
    )

    # Extended data (flexible JSON for additional signals)
    details_json = Column(
        JSON,
        nullable=True,
        comment="Additional risk details (alerts, forest type, etc.)"
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="eudr_georisk_snapshots")
    supply_site = relationship("EUDRSupplySite", back_populates="georisk_snapshots")

    __table_args__ = (
        Index('idx_eudr_georisk_tenant_site', 'tenant_id', 'supply_site_id'),
        Index('idx_eudr_georisk_tenant_date', 'tenant_id', 'snapshot_date'),
        Index('idx_eudr_georisk_site_date', 'supply_site_id', 'snapshot_date'),
    )

    def __repr__(self):
        return f"<EUDRGeoRiskSnapshot(id={self.id}, site_id={self.supply_site_id}, level={self.risk_level})>"


# =============================================================================
# EUDR DUE DILIGENCE (Tenant-owned)
# =============================================================================

class EUDRDueDiligence(Base):
    """
    EUDR due diligence statement covering a set of batches.

    Security: This is TENANT-OWNED data. All queries MUST filter by tenant_id.

    Represents a formal due diligence assessment required by EUDR for
    placing commodities on the EU market.
    """
    __tablename__ = "eudr_due_diligences"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Operator responsible for this DD
    operator_id = Column(
        Integer,
        ForeignKey("eudr_operators.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="EU operator/trader responsible"
    )

    # DD identification
    reference = Column(
        String(100),
        nullable=True,
        index=True,
        comment="User-facing due diligence statement ID"
    )

    # Commodity scope
    commodity_id = Column(
        Integer,
        ForeignKey("eudr_commodities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Period covered
    period_start = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Start of period covered"
    )
    period_end = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="End of period covered"
    )

    # Status
    status = Column(
        SQLEnum(EUDRDueDiligenceStatus),
        default=EUDRDueDiligenceStatus.DRAFT,
        nullable=False,
        index=True
    )

    # Aggregated risk assessment
    overall_risk_level = Column(
        SQLEnum(EUDRRiskLevel),
        nullable=True,
        comment="Overall risk level for this DD"
    )
    overall_risk_score = Column(
        Float,
        nullable=True,
        comment="Overall risk score (0-100)"
    )
    justification_summary = Column(
        Text,
        nullable=True,
        comment="Risk justification and mitigation summary"
    )

    # Aggregated metrics
    total_volume = Column(
        Float,
        default=0.0,
        comment="Total volume of all batches"
    )
    total_volume_unit = Column(
        String(20),
        default="tonne"
    )
    batch_count = Column(
        Integer,
        default=0,
        comment="Number of batches in this DD"
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="eudr_due_diligences")
    operator = relationship("EUDROperator", back_populates="due_diligences")
    commodity = relationship("EUDRCommodity", back_populates="due_diligences")
    batch_links = relationship(
        "EUDRDueDiligenceBatchLink",
        back_populates="due_diligence",
        cascade="all, delete-orphan"
    )
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    __table_args__ = (
        Index('idx_eudr_dd_tenant_status', 'tenant_id', 'status'),
        Index('idx_eudr_dd_tenant_operator', 'tenant_id', 'operator_id'),
        Index('idx_eudr_dd_tenant_commodity', 'tenant_id', 'commodity_id'),
        Index('idx_eudr_dd_tenant_period', 'tenant_id', 'period_start', 'period_end'),
        Index('idx_eudr_dd_tenant_ref', 'tenant_id', 'reference'),
    )

    def __repr__(self):
        return f"<EUDRDueDiligence(id={self.id}, ref={self.reference}, status={self.status.value})>"


# =============================================================================
# EUDR DUE DILIGENCE BATCH LINK (Tenant-owned via DD)
# =============================================================================

class EUDRDueDiligenceBatchLink(Base):
    """
    Links batches to due diligence statements with per-batch risk assessment.

    Security: This is TENANT-OWNED via parent due diligence.

    Each link represents a batch included in a due diligence statement,
    with its individual risk assessment.
    """
    __tablename__ = "eudr_due_diligence_batch_links"

    id = Column(Integer, primary_key=True, index=True)

    # Parent due diligence (provides tenant isolation)
    due_diligence_id = Column(
        Integer,
        ForeignKey("eudr_due_diligences.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Linked batch
    batch_id = Column(
        Integer,
        ForeignKey("eudr_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Per-batch risk assessment
    batch_risk_score = Column(
        Float,
        nullable=True,
        comment="Risk score for this batch (0-100)"
    )
    batch_risk_level = Column(
        SQLEnum(EUDRRiskLevel),
        nullable=True,
        comment="Risk level for this batch"
    )

    # Volume included (may be partial batch)
    included_volume = Column(
        Float,
        nullable=True,
        comment="Volume of batch included in this DD"
    )
    included_volume_unit = Column(
        String(20),
        default="tonne"
    )

    # Assessment notes
    assessment_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    due_diligence = relationship("EUDRDueDiligence", back_populates="batch_links")
    batch = relationship("EUDRBatch", back_populates="due_diligence_links")

    __table_args__ = (
        Index('idx_eudr_dd_batch_dd', 'due_diligence_id', 'batch_id', unique=True),
        Index('idx_eudr_dd_batch_risk', 'batch_risk_level'),
    )

    def __repr__(self):
        return f"<EUDRDueDiligenceBatchLink(dd_id={self.due_diligence_id}, batch_id={self.batch_id})>"
