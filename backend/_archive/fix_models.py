# fix_models.py - Fix model issues and complete setup
import os

print("🔧 Fixing model issues...")

# 1. Create the fixed payment model
payment_model = '''# app/models/payment.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
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
'''

with open('app/models/payment.py', 'w') as f:
    f.write(payment_model)
print("✅ Fixed payment.py model")

# 2. Create a simple data_quality model
data_quality_model = '''# app/models/data_quality.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class DataQualityScore(Base):
    __tablename__ = "data_quality_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to emission
    emission_id = Column(Integer, ForeignKey("emissions.id"))
    
    # Quality metrics
    completeness_score = Column(Float, default=0.0)
    accuracy_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    timeliness_score = Column(Float, default=0.0)
    
    # Overall score
    overall_score = Column(Float, default=0.0)
    
    # Details
    assessment_details = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    emission = relationship("Emission", back_populates="quality_scores")
'''

with open('app/models/data_quality.py', 'w') as f:
    f.write(data_quality_model)
print("✅ Created data_quality.py model")

# 3. Update the voucher model to fix relationship issues
voucher_fix = '''# app/models/voucher.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

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
    valid_until = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    used_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Status tracking
    status = Column(SQLEnum(VoucherStatus), default=VoucherStatus.VALID)
    is_expired = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    report_generation_in_progress = Column(Boolean, default=False)
    
    # Legacy fields for compatibility
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Created by
    permissions = Column(String, default="emissions_tracking")
    total_uses = Column(Integer, default=1)
    remaining_uses = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payment = relationship("Payment", back_populates="vouchers")
'''

with open('app/models/voucher.py', 'w') as f:
    f.write(voucher_fix)
print("✅ Updated voucher.py model")

# 4. Update emission model to add quality_scores relationship
emission_update = '''# Add this to your emission.py model in the Emission class:
    # quality_scores = relationship("DataQualityScore", back_populates="emission")
'''

print("\n📝 Note: Add this line to your Emission model:")
print('    quality_scores = relationship("DataQualityScore", back_populates="emission")')

print("\n✅ Model fixes complete!")
print("\nNow run: python final_setup.py")