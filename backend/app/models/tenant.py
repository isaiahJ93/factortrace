# app/models/tenant.py
"""
Tenant Model - Core multi-tenancy entity for FactorTrace.

Every tenant-owned record in the system references this table.
Tenants represent organizations/companies using the platform.

Security: This is the root entity for all tenant isolation.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Tenant(Base):
    """
    Tenant entity representing an organization using FactorTrace.

    All tenant-owned data (emissions, vouchers, payments, etc.) must have
    a foreign key to this table and must be filtered by tenant_id in all queries.
    """
    __tablename__ = "tenants"

    # Primary key - UUID for security (non-sequential)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Tenant identification
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-safe identifier

    # Billing integration
    stripe_customer_id = Column(String(255), nullable=True, unique=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Metadata
    settings = Column(Text, nullable=True)  # JSON blob for tenant-specific settings

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships (back_populates defined in child models)
    users = relationship("User", back_populates="tenant", lazy="dynamic")
    emissions = relationship("Emission", back_populates="tenant", lazy="dynamic")
    vouchers = relationship("Voucher", back_populates="tenant", lazy="dynamic")
    payments = relationship("Payment", back_populates="tenant", lazy="dynamic")

    # CBAM regime relationships
    cbam_declarations = relationship("CBAMDeclaration", back_populates="tenant", lazy="dynamic")
    cbam_installations = relationship("CBAMInstallation", back_populates="tenant", lazy="dynamic")

    # EUDR regime relationships
    eudr_operators = relationship("EUDROperator", back_populates="tenant", lazy="dynamic")
    eudr_supply_sites = relationship("EUDRSupplySite", back_populates="tenant", lazy="dynamic")
    eudr_batches = relationship("EUDRBatch", back_populates="tenant", lazy="dynamic")
    eudr_supply_chain_links = relationship("EUDRSupplyChainLink", back_populates="tenant", lazy="dynamic")
    eudr_georisk_snapshots = relationship("EUDRGeoRiskSnapshot", back_populates="tenant", lazy="dynamic")
    eudr_due_diligences = relationship("EUDRDueDiligence", back_populates="tenant", lazy="dynamic")

    def __repr__(self):
        return f"<Tenant {self.slug} ({self.id})>"

    @property
    def is_valid(self) -> bool:
        """Check if tenant is valid for operations."""
        return self.is_active
