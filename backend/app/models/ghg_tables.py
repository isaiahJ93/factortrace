# app/models/ghg_tables.py
"""
GHG Protocol Database Models - Multi-tenant enabled.

Security: All GHG queries MUST be filtered by tenant_id.
All models use tenant_id (not organization_id) for consistency.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, ForeignKey,
    JSON, Boolean, Index, Text, Date
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class GHGReportingPeriod(Base):
    """
    Reporting periods for GHG data.

    Security: All queries MUST be filtered by tenant_id.
    """
    __tablename__ = "ghg_reporting_periods"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    name = Column(String(255))
    start_date = Column(Date)
    end_date = Column(Date)

    __table_args__ = (
        Index('idx_ghg_rp_tenant', 'tenant_id'),
        {"extend_existing": True}
    )


class GHGEmissionFactor(Base):
    """
    Emission factors from various sources (GHG-specific).

    Note: This is separate from the main EmissionFactor table.
    Can be tenant-specific custom factors or global shared factors.
    """
    __tablename__ = "ghg_emission_factors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # MULTI-TENANT: Required for tenant isolation (nullable for global factors)
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,  # Nullable to allow global/shared factors
        index=True
    )

    category = Column(String(50), nullable=False)
    factor_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    source = Column(String(100))
    year = Column(Integer)
    region = Column(String(100))
    uncertainty_percentage = Column(Float)
    factor_emission_metadata = Column(JSON)

    __table_args__ = (
        Index('idx_ghg_ef_tenant_category', 'tenant_id', 'category'),
        Index('idx_ghg_ef_category_region', 'category', 'region'),
        {"extend_existing": True}
    )


class GHGActivityData(Base):
    """
    Activity data for GHG calculations.

    Security: All queries MUST be filtered by tenant_id.
    """
    __tablename__ = "ghg_activity_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    calculation_id = Column(String(36), ForeignKey("ghg_calculation_results.id"))
    category = Column(String(50), nullable=False)
    activity_type = Column(String(100))
    amount = Column(Float, nullable=False)
    data_quality_score = Column(Float)

    # Relationships
    calculation = relationship("GHGCalculationResult", back_populates="activity_data")

    __table_args__ = (
        Index('idx_ghg_ad_tenant_calc', 'tenant_id', 'calculation_id'),
        {"extend_existing": True}
    )


class GHGCalculationResult(Base):
    """
    GHG calculation results.

    Security: All queries MUST be filtered by tenant_id.
    """
    __tablename__ = "ghg_calculation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    reporting_period_start = Column(DateTime, nullable=False)
    reporting_period_end = Column(DateTime, nullable=False)
    total_emissions = Column(Float)
    calculation_method = Column(String(50))
    status = Column(String(50), default="pending")
    uncertainty_min = Column(Float)
    uncertainty_max = Column(Float)
    completed_at = Column(DateTime)

    # Relationships
    activity_data = relationship("GHGActivityData", back_populates="calculation")
    category_results = relationship("GHGCategoryResult", back_populates="calculation")

    __table_args__ = (
        Index('idx_ghg_cr_tenant_status', 'tenant_id', 'status'),
        Index('idx_ghg_cr_tenant_period', 'tenant_id', 'reporting_period_start'),
        {"extend_existing": True}
    )


class GHGCategoryResult(Base):
    """
    Category-level results for GHG calculations.

    Security: All queries MUST be filtered by tenant_id.
    """
    __tablename__ = "ghg_category_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    calculation_id = Column(String(36), ForeignKey("ghg_calculation_results.id"))
    emissions_co2e = Column(Float, nullable=False)
    calculation_details = Column(JSON)

    # Relationships
    calculation = relationship("GHGCalculationResult", back_populates="category_results")

    __table_args__ = (
        Index('idx_ghg_catr_tenant_calc', 'tenant_id', 'calculation_id'),
        {"extend_existing": True}
    )


class GHGDataQualityScore(Base):
    """
    Data quality scores for GHG data.

    Security: All queries MUST be filtered by tenant_id.
    """
    __tablename__ = "ghg_data_quality_scores"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    calculation_id = Column(String(36))
    score = Column(Float)
    criteria = Column(String(255))

    __table_args__ = (
        Index('idx_ghg_dqs_tenant', 'tenant_id'),
        {"extend_existing": True}
    )


class GHGScope3Inventory(Base):
    """
    Scope 3 inventory for a tenant.

    Security: All queries MUST be filtered by tenant_id.
    """
    __tablename__ = "ghg_scope3_inventories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    year = Column(Integer, nullable=False)
    total_scope3_emissions = Column(Float)
    verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)

    __table_args__ = (
        Index('idx_ghg_s3i_tenant_year', 'tenant_id', 'year'),
        {"extend_existing": True}
    )


class GHGAuditLog(Base):
    """
    Audit log for GHG data changes.

    Security: All queries MUST be filtered by tenant_id.
    Super-admin access to cross-tenant logs must be audit-logged separately.
    """
    __tablename__ = "ghg_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    entity_type = Column(String(100))
    entity_id = Column(String(36))
    action = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(36))
    changes = Column(Text)

    __table_args__ = (
        Index('idx_ghg_audit_tenant_entity', 'tenant_id', 'entity_type'),
        Index('idx_ghg_audit_tenant_time', 'tenant_id', 'timestamp'),
        {"extend_existing": True}
    )


# Model aliases for backward compatibility
# DEPRECATED: Use the class names directly
OrganizationDB = None  # Removed - use Tenant instead
EmissionFactorDB = GHGEmissionFactor
ActivityDataDB = GHGActivityData
CalculationResultDB = GHGCalculationResult
Scope3InventoryDB = GHGScope3Inventory
ReportingPeriodDB = GHGReportingPeriod
DataQualityScoreDB = GHGDataQualityScore
AuditLogDB = GHGAuditLog
