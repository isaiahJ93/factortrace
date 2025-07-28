# fix_user_id_type.py - Fix the user ID type mismatch
import os

print("🔧 Fixing user ID type mismatch...")

# Check current user model
user_model_path = "app/models/user.py"

# Read current content
with open(user_model_path, 'r') as f:
    content = f.read()

# Check if it's using String for ID
if "id = Column(String" in content:
    print("Found String ID in User model, fixing...")
    
    # Replace String ID with Integer ID
    new_content = content.replace(
        "id = Column(String, primary_key=True",
        "id = Column(Integer, primary_key=True"
    )
    
    # Remove UUID generation
    new_content = new_content.replace('''def __init__(self, **kwargs):
        if 'id' not in kwargs:
            import uuid
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)''', '')
    
    # Write back
    with open(user_model_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Fixed User model to use Integer ID")
else:
    print("✅ User model already uses Integer ID")

# Now fix the voucher model to match
voucher_model = '''# app/models/voucher.py
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
    used_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Changed to Integer
    
    # Status tracking
    status = Column(SQLEnum(VoucherStatus), default=VoucherStatus.VALID)
    is_expired = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    report_generation_in_progress = Column(Boolean, default=False)
    
    # Legacy fields for compatibility
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Changed to Integer
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
    f.write(voucher_model)

print("✅ Fixed Voucher model to use Integer foreign keys")

print("\n✅ All fixes complete!")
print("\nNow you need to:")
print("1. Drop and recreate the database:")
print("   dropdb factortrace")
print("   createdb factortrace")
print("2. Run setup again:")
print("   python final_setup.py")