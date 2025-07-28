#!/usr/bin/env python3
"""Minimal GHG test"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.ghg_tables import GHGOrganization, GHGEmissionFactor
from app.core.config import settings

def test_minimal():
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print(f"Database: {settings.DATABASE_URL}")
    
    # Check tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nTables: {', '.join(tables)}")
    
    # Check if GHG tables exist
    ghg_tables = [t for t in tables if 'ghg_' in t]
    print(f"\nGHG tables: {', '.join(ghg_tables)}")
    
    # Check organization
    org_count = session.query(GHGOrganization).count()
    print(f"\nOrganizations: {org_count}")
    
    # Check emission factors
    factor_count = session.query(GHGEmissionFactor).count()
    print(f"Emission factors: {factor_count}")
    
    session.close()

if __name__ == "__main__":
    test_minimal()
