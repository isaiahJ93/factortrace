#!/usr/bin/env python3
"""
Complete fix for all FactorTrace models and setup
Fixes ID type mismatches and missing imports
"""

import os
import re
from pathlib import Path

def fix_model_imports(file_path):
    """Fix missing imports in a model file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if file uses SQLAlchemy types without importing them
    needs_imports = []
    
    if 'Column(' in content and 'from sqlalchemy import' not in content:
        needs_imports.append('Column')
    
    # Check for each type
    types_to_check = [
        'Integer', 'String', 'Boolean', 'DateTime', 'Float', 'Text',
        'ForeignKey', 'Enum', 'JSON', 'Date', 'Time', 'Numeric'
    ]
    
    for type_name in types_to_check:
        if re.search(rf'\b{type_name}\b', content) and f'import {type_name}' not in content:
            needs_imports.append(type_name)
    
    if needs_imports:
        # Build import statement
        import_line = f"from sqlalchemy import {', '.join(needs_imports)}\n"
        
        # Add after existing sqlalchemy imports or at the beginning
        if 'from sqlalchemy' in content:
            # Find the last sqlalchemy import
            lines = content.split('\n')
            last_import_idx = -1
            for i, line in enumerate(lines):
                if 'from sqlalchemy' in line:
                    last_import_idx = i
            
            if last_import_idx >= 0:
                lines.insert(last_import_idx + 1, import_line.strip())
                content = '\n'.join(lines)
        else:
            # Add at the beginning after the module docstring
            lines = content.split('\n')
            insert_idx = 0
            
            # Skip docstring if present
            if lines[0].startswith('"""'):
                for i, line in enumerate(lines[1:], 1):
                    if '"""' in line:
                        insert_idx = i + 1
                        break
            
            lines.insert(insert_idx, import_line.strip())
            content = '\n'.join(lines)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Fixed imports in {file_path.name}")

def create_missing_models():
    """Create any missing model files"""
    models_dir = Path("app/models")
    
    # Create Payment model if missing
    payment_path = models_dir / "payment.py"
    if not payment_path.exists():
        payment_content = '''"""Payment model for Stripe integration"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Stripe fields
    stripe_payment_intent_id = Column(String, unique=True, index=True)
    stripe_checkout_session_id = Column(String, unique=True, index=True)
    stripe_customer_id = Column(String, index=True)
    
    # Payment details
    amount = Column(Float, nullable=False)  # Amount in cents
    currency = Column(String, default="eur")
    status = Column(String, default="pending")  # pending, succeeded, failed
    
    # Customer info
    customer_email = Column(String, nullable=False)
    customer_name = Column(String)
    
    # Metadata
    metadata = Column(Text)  # JSON string
    
    # Webhook tracking
    webhook_received = Column(Boolean, default=False)
    webhook_processed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vouchers = relationship("Voucher", back_populates="payment")
'''
        payment_path.write_text(payment_content)
        print("✅ Created Payment model")
    
    # Ensure __init__.py exports all models
    init_path = models_dir / "__init__.py"
    init_content = '''"""Models package"""
from .user import User
from .voucher import Voucher
from .payment import Payment
from .emission import Emission
from .emission_factor import EmissionFactor

__all__ = ["User", "Voucher", "Payment", "Emission", "EmissionFactor"]
'''
    init_path.write_text(init_content)
    print("✅ Updated models __init__.py")

def fix_user_model():
    """Specifically fix the User model"""
    user_path = Path("app/models/user.py")
    if user_path.exists():
        content = '''"""User model"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    
    # Profile
    company_name = Column(String)
    full_name = Column(String)
    
    # Auth
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    emissions = relationship("Emission", back_populates="user", cascade="all, delete-orphan")
'''
        user_path.write_text(content)
        print("✅ Fixed User model")

def fix_voucher_model():
    """Fix the Voucher model"""
    voucher_path = Path("app/models/voucher.py")
    if voucher_path.exists():
        content = '''"""Voucher model"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
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
'''
        
        # Need to import Base
        content = content.replace(
            'import enum',
            'import enum\nfrom app.core.database import Base'
        )
        
        voucher_path.write_text(content)
        print("✅ Fixed Voucher model")

def main():
    print("🔧 Fixing all FactorTrace models...\n")
    
    # Create missing models first
    create_missing_models()
    
    # Fix specific models
    fix_user_model()
    fix_voucher_model()
    
    # Fix imports in all model files
    models_dir = Path("app/models")
    for model_file in models_dir.glob("*.py"):
        if model_file.name != "__init__.py":
            fix_model_imports(model_file)
    
    print("\n✅ All fixes complete!")
    print("\nNow run:")
    print("  python final_setup.py")

if __name__ == "__main__":
    main()