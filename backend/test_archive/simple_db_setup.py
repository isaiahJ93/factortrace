#!/usr/bin/env python3
"""
Simple database setup for FactorTrace
Creates all tables without complex imports
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

def setup_database():
    """Create all database tables"""
    print("🚀 Simple FactorTrace Database Setup\n")
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL", "postgresql://localhost/factortrace")
    print(f"📊 Using database: {database_url}\n")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Import Base and create tables
    try:
        from app.core.database import Base
        
        # Import all models to register them with Base
        print("📦 Loading models...")
        
        # Try to import each model individually
        models_imported = 0
        
        try:
            from app.models.user import User
            models_imported += 1
            print("  ✅ User model")
        except Exception as e:
            print(f"  ❌ User model: {e}")
        
        try:
            from app.models.payment import Payment
            models_imported += 1
            print("  ✅ Payment model")
        except Exception as e:
            print(f"  ❌ Payment model: {e}")
        
        try:
            from app.models.voucher import Voucher
            models_imported += 1
            print("  ✅ Voucher model")
        except Exception as e:
            print(f"  ❌ Voucher model: {e}")
        
        try:
            from app.models.emission import Emission
            models_imported += 1
            print("  ✅ Emission model")
        except Exception as e:
            print(f"  ❌ Emission model: {e}")
        
        try:
            from app.models.emission_factor import EmissionFactor
            models_imported += 1
            print("  ✅ EmissionFactor model")
        except Exception as e:
            print(f"  ❌ EmissionFactor model: {e}")
        
        print(f"\n📊 Imported {models_imported} models")
        
        # Create all tables
        print("\n🔨 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  - {table}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def create_test_data():
    """Create some test data"""
    from sqlalchemy.orm import sessionmaker
    from app.models.user import User
    from app.models.emission_factor import EmissionFactor
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create test user
        test_user = User(
            email="test@factortrace.com",
            company_name="Test Company",
            full_name="Test User",
            is_active=True
        )
        session.add(test_user)
        
        # Create some emission factors
        factors = [
            {"name": "Electricity", "category": "Energy", "factor": 0.5, "unit": "kgCO2/kWh"},
            {"name": "Natural Gas", "category": "Energy", "factor": 2.0, "unit": "kgCO2/m3"},
            {"name": "Petrol", "category": "Transport", "factor": 2.3, "unit": "kgCO2/L"},
        ]
        
        for factor_data in factors:
            factor = EmissionFactor(**factor_data)
            session.add(factor)
        
        session.commit()
        print("\n✅ Created test data")
        
    except Exception as e:
        session.rollback()
        print(f"\n⚠️  Could not create test data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # First run the fix script
    print("🔧 Running model fixes first...\n")
    os.system("python fix_all_models.py")
    
    print("\n" + "="*50 + "\n")
    
    # Then setup database
    if setup_database():
        print("\n✅ Setup complete! You can now run:")
        print("  uvicorn app.main:app --reload")
    else:
        print("\n❌ Setup failed. Please check the errors above.")