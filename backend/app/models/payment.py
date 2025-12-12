# app/models/payment.py
"""Payment model - Multi-tenant enabled.

Security: All payment queries MUST be filtered by tenant_id.
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Base):
    """
    Payment entity for Stripe transactions.

    Security: All payment queries MUST be filtered by tenant_id.
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    # MULTI-TENANT: Required for tenant isolation
    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Stripe fields
    stripe_session_id = Column(String, unique=True, index=True)
    stripe_payment_intent = Column(String, unique=True, index=True)

    # Payment details
    amount = Column(Integer)  # Amount in cents
    currency = Column(String, default="EUR")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, index=True)

    # Customer info
    customer_email = Column(String, index=True)
    payment_metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="payments")
    vouchers = relationship("Voucher", back_populates="payment")

    # Indexes for performance - tenant_id first for multi-tenant queries
    __table_args__ = (
        Index('idx_payments_tenant_status', 'tenant_id', 'status'),
        Index('idx_payments_tenant_created', 'tenant_id', 'created_at'),
    )
