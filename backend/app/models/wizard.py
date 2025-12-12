# app/models/wizard.py
"""
Self-Serve Compliance Wizard Models.

Provides the ComplianceWizardSession model for tracking supplier onboarding
through the "€500 magic moment" - email to compliance report in 10 minutes.

Reference: docs/regimes/csrd.md
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Text,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class WizardStatus(str, enum.Enum):
    """Status of a compliance wizard session."""
    DRAFT = "draft"              # Session created but not started
    IN_PROGRESS = "in_progress"  # User is actively filling data
    COMPLETED = "completed"      # Report generated successfully
    ABANDONED = "abandoned"      # Session timed out or user left


class ComplianceWizardSession(Base):
    """
    Tracks a supplier's journey through the self-serve compliance wizard.

    The wizard guides Tier 2 suppliers from voucher redemption to a
    complete CSRD-compliant Scope 3 report in approximately 10 minutes.

    Multi-tenant: Each session is scoped to a tenant via tenant_id.
    """
    __tablename__ = "compliance_wizard_sessions"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant isolation (CRITICAL)
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Voucher that initiated this wizard session
    voucher_id = Column(
        Integer,
        ForeignKey("vouchers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Session status
    status = Column(
        SQLEnum(WizardStatus),
        default=WizardStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Current step in the wizard (for resumption)
    current_step = Column(String(50), default="company_profile", nullable=False)

    # Company profile (Step 1)
    # JSON: {name, country, industry_nace, employees, annual_revenue_eur, ...}
    company_profile = Column(JSON, nullable=True)

    # Activity data collected (Step 2)
    # JSON: {electricity_kwh, natural_gas_m3, diesel_l, petrol_l,
    #        business_travel_km, employee_commute_km, waste_kg, water_m3,
    #        purchased_goods_eur, ...}
    activity_data = Column(JSON, nullable=True)

    # Calculated emissions (computed after Step 2)
    # JSON: {scope1_tco2e, scope2_tco2e, scope3_tco2e, total_tco2e,
    #        breakdown: [{category, amount, factor_used, dataset}, ...]}
    calculated_emissions = Column(JSON, nullable=True)

    # Industry template used (if any)
    template_id = Column(String(50), nullable=True, index=True)

    # Generated report reference (stored as ID for now, no FK constraint)
    # This allows future Report model to be added without migration dependency
    report_id = Column(Integer, nullable=True, index=True)

    # Audit notes / calculation methodology notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Track which user created the session
    created_by_user_id = Column(Integer, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="wizard_sessions")
    voucher = relationship("Voucher", back_populates="wizard_session")

    # Indexes for performance - tenant_id first for multi-tenant queries
    __table_args__ = (
        Index('idx_wizard_sessions_tenant_status', 'tenant_id', 'status'),
        Index('idx_wizard_sessions_tenant_voucher', 'tenant_id', 'voucher_id'),
    )

    def __repr__(self) -> str:
        return f"<ComplianceWizardSession(id={self.id}, tenant_id={self.tenant_id}, status={self.status})>"


class IndustryTemplate(Base):
    """
    Pre-configured industry templates with typical activity categories
    and smart defaults for common supplier types.

    These are reference data (not tenant-owned) - shared across all tenants.
    """
    __tablename__ = "industry_templates"

    # Primary key (using string ID for easy reference, e.g., "manufacturing_small")
    id = Column(String(50), primary_key=True)

    # Display name
    name = Column(String(200), nullable=False)

    # NACE code or codes this template applies to
    # JSON: ["C10", "C11", "C12"] for manufacturing subcategories
    nace_codes = Column(JSON, nullable=False)

    # Description of what this template is for
    description = Column(Text, nullable=True)

    # Company size range this template is optimized for
    # "micro" (1-9), "small" (10-49), "medium" (50-249), "large" (250+)
    company_size = Column(String(20), nullable=True)

    # Default activity categories to show
    # JSON: ["electricity", "natural_gas", "diesel", "business_travel", ...]
    activity_categories = Column(JSON, nullable=False)

    # Smart defaults for this industry
    # JSON: {electricity_kwh_per_employee: 2500, gas_m3_per_sqm: 15, ...}
    smart_defaults = Column(JSON, nullable=True)

    # Typical emission factor datasets to use
    # JSON: {scope1: "DEFRA_2024", scope2: "DEFRA_2024", scope3: "EXIOBASE_2020"}
    recommended_datasets = Column(JSON, nullable=True)

    # Ordering for UI display
    display_order = Column(Integer, default=100)

    # Active flag
    is_active = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<IndustryTemplate(id={self.id}, name={self.name})>"
