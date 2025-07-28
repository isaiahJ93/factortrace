#!/usr/bin/env python3
"""Populate sample GHG data - Fixed for PostgreSQL"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.ghg_tables import GHGEmissionFactor, GHGOrganization
from app.schemas.ghg_schemas import Scope3Category
from app.core.config import settings
import uuid

def populate_emission_factors():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if organization already exists
        org_id = "12345678-1234-5678-1234-567812345678"  # String for SQLite
        existing_org = db.query(GHGOrganization).filter(GHGOrganization.id == org_id).first()
        
        if not existing_org:
            # Add a sample organization
            org = GHGOrganization(
                id=org_id,
                name="Sample Company",
                industry="Technology",
                country="US"
            )
            db.add(org)
            db.commit()
            print(f"✅ Created organization: {org.name}")
        else:
            print(f"Organization already exists: {existing_org.name}")
        
        # Check if emission factors already exist
        existing_factors = db.query(GHGEmissionFactor).first()
        if existing_factors:
            print("Emission factors already exist, skipping...")
            return
        
        # Sample emission factors
        factors = [
            {
                "name": "Purchased Goods - Electronics",
                "category": Scope3Category.PURCHASED_GOODS.value,
                "factor_value": 2.8,
                "unit": "kg CO2e/USD",
                "source": "EPA",
                "year": 2024,
                "region": "US"
            },
            {
                "name": "Business Travel - Air",
                "category": Scope3Category.BUSINESS_TRAVEL.value,
                "factor_value": 0.15,
                "unit": "kg CO2e/km",
                "source": "DEFRA",
                "year": 2024,
                "region": "Global"
            },
            {
                "name": "Waste - Landfill",
                "category": Scope3Category.WASTE.value,
                "factor_value": 0.467,
                "unit": "kg CO2e/kg",
                "source": "EPA",
                "year": 2024,
                "region": "US"
            },
            {
                "name": "Transport - Road Freight",
                "category": Scope3Category.UPSTREAM_TRANSPORT.value,
                "factor_value": 0.12,
                "unit": "kg CO2e/ton-km",
                "source": "DEFRA",
                "year": 2024,
                "region": "Global"
            }
        ]
        
        for factor_data in factors:
            factor = GHGEmissionFactor(**factor_data)
            db.add(factor)
        
        db.commit()
        print(f"✅ Created {len(factors)} emission factors")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_emission_factors()
