#!/usr/bin/env python3
"""Populate sample GHG data"""

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
    
    # Check if data already exists
    existing = db.query(GHGEmissionFactor).first()
    if existing:
        print("Data already exists, skipping...")
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
    
    # Add a sample organization
    org = GHGOrganization(
        id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        name="Sample Company",
        industry="Technology",
        country="US"
    )
    db.add(org)
    
    try:
        db.commit()
        print("✅ Sample data populated successfully")
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_emission_factors()
