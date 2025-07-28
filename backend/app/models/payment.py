# app/models/payment.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, String, DateTime, Float, Enum, JSON
from sqlalchemy import String, DateTime, Float, Enum, JSON
from app.core.database import Base
from datetime import datetime
import enum

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Stripe fields
    stripe_session_id = Column(String, unique=True, index=True)
    stripe_payment_intent = Column(String, unique=True, index=True)
    
    # Payment details
    amount = Column(Integer)  # Amount in cents
    currency = Column(String, default="EUR")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    
    # Customer info
    customer_email = Column(String, index=True)
    payment_metadata = Column(JSON, default=dict)  # Changed from 'metadata' to 'payment_metadata'
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vouchers = relationship("Voucher", back_populates="payment")
