# app/models/cbam.py
"""
CBAM (Carbon Border Adjustment Mechanism) Models - Multi-tenant enabled.

Implements the EU CBAM Regulation (EU) 2023/956 for tracking embedded emissions
in imported goods. Supports product-level embedded emissions calculation and
declaration workflows.

Security: All tenant-owned CBAM data queries MUST be filtered by tenant_id.

Reference: docs/regimes/cbam.md
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

class CBAMDeclarationStatus(str, enum.Enum):
    """Status of a CBAM declaration."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    AMENDED = "amended"
    VERIFIED = "verified"
    ARCHIVED = "archived"


class CBAMFactorDataset(str, enum.Enum):
    """
    Emission factor dataset sources for CBAM calculations.

    - CBAM_DEFAULT: EU default factors from official CBAM regulation
    - CBAM_PLANT_SPECIFIC: Verified plant/installation-specific factors
    - EXIOBASE_2020: EXIOBASE 3 spend-based factors (fallback)
    """
    CBAM_DEFAULT = "CBAM_DEFAULT"
    CBAM_PLANT_SPECIFIC = "CBAM_PLANT_SPECIFIC"
    EXIOBASE_2020 = "EXIOBASE_2020"


class CBAMProductSector(str, enum.Enum):
    """
    CBAM product sectors as defined in the regulation.
    V1 focuses on the initial CBAM scope.
    """
    IRON_STEEL = "iron_steel"
    ALUMINIUM = "aluminium"
    CEMENT = "cement"
    FERTILISERS = "fertilisers"
    ELECTRICITY = "electricity"
    HYDROGEN = "hydrogen"


# =============================================================================
# CBAM FACTOR SOURCE (Reference Data - Not tenant-owned)
# =============================================================================

class CBAMFactorSource(Base):
    """
    Reference table for CBAM emission factor sources/datasets.

    This is SHARED reference data (not tenant-owned).
    Used to track which dataset was used for each calculation.
    """
    __tablename__ = "cbam_factor_sources"

    id = Column(Integer, primary_key=True, index=True)

    # Dataset identification
    dataset = Column(
        SQLEnum(CBAMFactorDataset),
        nullable=False,
        index=True,
        comment="Dataset identifier (CBAM_DEFAULT, CBAM_PLANT_SPECIFIC, EXIOBASE_2020)"
    )
    version = Column(
        String(50),
        nullable=False,
        comment="Version of the dataset (e.g., '2024_Q1', 'v1.0')"
    )

    # Metadata
    description = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=True, comment="Official source URL")
    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_cbam_factor_source_dataset_version', 'dataset', 'version', unique=True),
    )

    def __repr__(self):
        return f"<CBAMFactorSource(dataset={self.dataset.value}, version={self.version})>"


# =============================================================================
# CBAM PRODUCT (Reference Data - Not tenant-owned)
# =============================================================================

class CBAMProduct(Base):
    """
    CBAM product definitions with CN (Combined Nomenclature) codes.

    This is SHARED reference data (not tenant-owned).
    Maps CN product codes to emission factors and calculation methods.

    CN codes are 8-10 character codes used in EU customs declarations.
    """
    __tablename__ = "cbam_products"

    id = Column(Integer, primary_key=True, index=True)

    # Product identification
    cn_code = Column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        comment="Combined Nomenclature code (8-10 chars)"
    )
    description = Column(String(500), nullable=False)

    # Sector classification
    sector = Column(
        SQLEnum(CBAMProductSector),
        nullable=False,
        index=True,
        comment="CBAM product sector"
    )

    # Default emission factor (can be overridden by plant-specific)
    default_factor_id = Column(
        Integer,
        ForeignKey("emission_factors.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK to default emission factor"
    )

    # Unit of measurement for this product
    unit = Column(
        String(20),
        nullable=False,
        default="tonne",
        comment="Standard unit for quantity (tonne, kg, MWh)"
    )

    # Additional metadata
    hs_code = Column(
        String(6),
        nullable=True,
        index=True,
        comment="Harmonized System code (6 chars, broader category)"
    )
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, comment="Whether this product is currently in CBAM scope")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    default_factor = relationship("EmissionFactor", foreign_keys=[default_factor_id])
    declaration_lines = relationship("CBAMDeclarationLine", back_populates="product")

    __table_args__ = (
        Index('idx_cbam_product_sector_active', 'sector', 'is_active'),
    )

    def __repr__(self):
        return f"<CBAMProduct(cn_code={self.cn_code}, sector={self.sector.value})>"


# =============================================================================
# CBAM DECLARATION (Tenant-owned)
# =============================================================================

class CBAMDeclaration(Base):
    """
    CBAM declaration for a reporting period.

    Security: This is TENANT-OWNED data. All queries MUST filter by tenant_id.

    A declaration represents a complete CBAM submission for an importer
    covering a specific reporting period.
    """
    __tablename__ = "cbam_declarations"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Declaration identification
    declaration_reference = Column(
        String(100),
        nullable=True,
        index=True,
        comment="User-supplied or auto-generated reference number"
    )

    # Reporting period
    period_start = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Start of reporting period"
    )
    period_end = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="End of reporting period"
    )

    # Status tracking
    status = Column(
        SQLEnum(CBAMDeclarationStatus),
        default=CBAMDeclarationStatus.DRAFT,
        nullable=False,
        index=True
    )

    # Aggregated totals (calculated from lines)
    total_embedded_emissions_tco2e = Column(
        Float,
        default=0.0,
        comment="Total embedded emissions in tCO2e (sum of all lines)"
    )
    total_quantity = Column(
        Float,
        default=0.0,
        comment="Total quantity of goods (in primary unit)"
    )

    # Importer information
    importer_name = Column(String(200), nullable=True)
    importer_eori = Column(
        String(17),
        nullable=True,
        index=True,
        comment="Economic Operators Registration and Identification number"
    )
    importer_country = Column(String(2), nullable=True, comment="ISO 2-letter country code")

    # Verification
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(200), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)

    # Submission tracking
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    submission_reference = Column(String(100), nullable=True, comment="Official submission ID from EU system")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="cbam_declarations")
    lines = relationship(
        "CBAMDeclarationLine",
        back_populates="declaration",
        cascade="all, delete-orphan"
    )
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    # Indexes for performance - tenant_id first for multi-tenant queries
    __table_args__ = (
        Index('idx_cbam_declaration_tenant_status', 'tenant_id', 'status'),
        Index('idx_cbam_declaration_tenant_period', 'tenant_id', 'period_start', 'period_end'),
        Index('idx_cbam_declaration_tenant_ref', 'tenant_id', 'declaration_reference'),
    )

    def __repr__(self):
        return f"<CBAMDeclaration(id={self.id}, ref={self.declaration_reference}, status={self.status.value})>"

    @property
    def line_count(self) -> int:
        """Number of line items in this declaration."""
        return len(self.lines) if self.lines else 0

    def recalculate_totals(self):
        """Recalculate aggregated totals from line items."""
        if self.lines:
            self.total_embedded_emissions_tco2e = sum(
                line.embedded_emissions_tco2e or 0 for line in self.lines
            )
            self.total_quantity = sum(
                line.quantity or 0 for line in self.lines
            )
        else:
            self.total_embedded_emissions_tco2e = 0.0
            self.total_quantity = 0.0


# =============================================================================
# CBAM DECLARATION LINE (Tenant-owned via declaration)
# =============================================================================

class CBAMDeclarationLine(Base):
    """
    Individual line item in a CBAM declaration.

    Security: This is TENANT-OWNED via parent declaration.
    Access control enforced through CBAMDeclaration.tenant_id.

    Each line represents a specific product import with calculated
    embedded emissions.
    """
    __tablename__ = "cbam_declaration_lines"

    id = Column(Integer, primary_key=True, index=True)

    # Parent declaration (provides tenant isolation)
    declaration_id = Column(
        Integer,
        ForeignKey("cbam_declarations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Product identification
    cbam_product_id = Column(
        Integer,
        ForeignKey("cbam_products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="FK to CBAM product (CN code)"
    )

    # Origin information
    country_of_origin = Column(
        String(2),
        nullable=False,
        index=True,
        comment="ISO 2-letter country code of production"
    )
    facility_id = Column(
        String(100),
        nullable=True,
        comment="Installation/facility identifier (if known)"
    )
    facility_name = Column(String(200), nullable=True)

    # Quantity
    quantity = Column(
        Float,
        nullable=False,
        comment="Quantity of goods imported"
    )
    quantity_unit = Column(
        String(20),
        nullable=False,
        default="tonne",
        comment="Unit of quantity (must match product unit)"
    )

    # Emission calculation results
    embedded_emissions_tco2e = Column(
        Float,
        nullable=True,
        comment="Calculated embedded emissions in tCO2e"
    )
    emission_factor_value = Column(
        Float,
        nullable=True,
        comment="Emission factor used (tCO2e per unit)"
    )
    emission_factor_unit = Column(
        String(50),
        nullable=True,
        comment="Unit of emission factor (e.g., tCO2e/tonne)"
    )

    # Factor source tracking
    emission_factor_id = Column(
        Integer,
        ForeignKey("emission_factors.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK to emission factor used"
    )
    factor_dataset = Column(
        SQLEnum(CBAMFactorDataset),
        nullable=True,
        comment="Which dataset the factor came from"
    )
    is_default_factor = Column(
        Boolean,
        default=True,
        comment="True if EU default factor used, False if plant-specific"
    )

    # Evidence and documentation
    evidence_reference = Column(
        String(500),
        nullable=True,
        comment="Reference to supporting documentation"
    )
    evidence_document_id = Column(
        Integer,
        ForeignKey("evidence_documents.id", ondelete="SET NULL"),
        nullable=True
    )

    # Calculation metadata
    calculation_date = Column(DateTime(timezone=True), nullable=True)
    calculation_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    declaration = relationship("CBAMDeclaration", back_populates="lines")
    product = relationship("CBAMProduct", back_populates="declaration_lines")
    emission_factor = relationship("EmissionFactor", foreign_keys=[emission_factor_id])
    evidence_document = relationship("EvidenceDocument", foreign_keys=[evidence_document_id])

    # Indexes for performance
    __table_args__ = (
        Index('idx_cbam_line_declaration_product', 'declaration_id', 'cbam_product_id'),
        Index('idx_cbam_line_country', 'country_of_origin'),
        Index('idx_cbam_line_factor_dataset', 'factor_dataset'),
    )

    def __repr__(self):
        return f"<CBAMDeclarationLine(id={self.id}, product_id={self.cbam_product_id}, qty={self.quantity})>"

    def calculate_emissions(self, factor_value: float, factor_unit: str, dataset: CBAMFactorDataset):
        """
        Calculate embedded emissions for this line item.

        Args:
            factor_value: Emission factor value (tCO2e per unit)
            factor_unit: Unit of the emission factor
            dataset: Source dataset for the factor
        """
        self.emission_factor_value = factor_value
        self.emission_factor_unit = factor_unit
        self.factor_dataset = dataset
        self.embedded_emissions_tco2e = self.quantity * factor_value
        self.calculation_date = datetime.utcnow()
        self.is_default_factor = (dataset == CBAMFactorDataset.CBAM_DEFAULT)


# =============================================================================
# CBAM INSTALLATION (Optional - for plant-specific factors)
# =============================================================================

class CBAMInstallation(Base):
    """
    CBAM installation/facility for plant-specific emission factors.

    Security: This is TENANT-OWNED data for tracking supplier installations.

    Installations are production facilities in third countries that can
    provide plant-specific emission factors instead of EU defaults.
    """
    __tablename__ = "cbam_installations"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Installation identification
    installation_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="External installation identifier"
    )
    name = Column(String(200), nullable=False)

    # Location
    country = Column(String(2), nullable=False, index=True, comment="ISO 2-letter country code")
    region = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)

    # Operator information
    operator_name = Column(String(200), nullable=True)
    operator_id = Column(String(100), nullable=True)

    # Sector and products
    sector = Column(
        SQLEnum(CBAMProductSector),
        nullable=False,
        index=True
    )

    # Plant-specific emission intensity
    specific_emission_factor = Column(
        Float,
        nullable=True,
        comment="Plant-specific emission factor (tCO2e per unit)"
    )
    specific_factor_unit = Column(String(50), nullable=True)
    specific_factor_valid_from = Column(DateTime(timezone=True), nullable=True)
    specific_factor_valid_to = Column(DateTime(timezone=True), nullable=True)

    # Verification
    is_verified = Column(Boolean, default=False)
    verification_body = Column(String(200), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    verification_reference = Column(String(200), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="cbam_installations")

    # Indexes
    __table_args__ = (
        Index('idx_cbam_installation_tenant_country', 'tenant_id', 'country'),
        Index('idx_cbam_installation_tenant_sector', 'tenant_id', 'sector'),
        Index('idx_cbam_installation_tenant_id', 'tenant_id', 'installation_id', unique=True),
    )

    def __repr__(self):
        return f"<CBAMInstallation(id={self.id}, name={self.name}, country={self.country})>"
