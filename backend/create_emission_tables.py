# backend/create_emission_tables.py
"""
Safe script to create emission factor tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect
from app.db.base import Base
from app.db.session import SQLALCHEMY_DATABASE_URL

# Import all models to ensure they're registered with Base
from app.models.user import User
from app.models.emission import Emission
from app.models.emission_factor import EmissionFactor

def create_emission_tables():
    """Create only the emission_factors table if it doesn't exist"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Check existing tables
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"Existing tables: {existing_tables}")
    
    # Create tables (SQLAlchemy will only create non-existing ones)
    Base.metadata.create_all(bind=engine, checkfirst=True)
    
    # Verify creation
    inspector = inspect(engine)
    tables_after = inspector.get_table_names()
    print(f"Tables after creation: {tables_after}")
    
    if 'emission_factors' in tables_after:
        print("✅ emission_factors table ready!")
    else:
        print("❌ Failed to create emission_factors table")

if __name__ == "__main__":
    create_emission_tables()