"""User model - Multi-tenant user accounts."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    User entity belonging to a tenant.

    Security: All user queries must be scoped by tenant_id.
    Super-admins (is_super_admin=True) can access cross-tenant data.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    email = Column(String, unique=True, nullable=False, index=True)

    # Profile
    company_name = Column(String)
    full_name = Column(String)

    # Auth
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)  # Tenant-level admin
    is_super_admin = Column(Boolean, default=False)  # Platform-level super-admin (cross-tenant)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    emissions = relationship("Emission", back_populates="user", cascade="all, delete-orphan")
