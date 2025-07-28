"""Voucher model"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Enum
from datetime import datetime
import enum
from app.core.database import Base

class VoucherStatus(str, enum.Enum):
    VALID = "VALID"
    USED = "USED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

class Voucher(Base):
    __tablename__ = "vouchers"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    
    # Payment relationship
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    
    # Company info
    company_email = Column(String, index=True)
    company_name = Column(String)
    
    # Validity
    valid_until = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    used_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status tracking
    status = Column(SQLEnum(VoucherStatus), default=VoucherStatus.VALID)
    is_expired = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    report_generation_in_progress = Column(Boolean, default=False)
    
    # Legacy fields
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    permissions = Column(String, default="emissions_tracking")
    total_uses = Column(Integer, default=1)
    remaining_uses = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payment = relationship("Payment", back_populates="vouchers")
    user = relationship("User", foreign_keys=[used_by_user_id])
