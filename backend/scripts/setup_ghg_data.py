#!/usr/bin/env python3
"""Setup all GHG data"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.ghg_tables import GHGOrganization, GHGEmissionFactor
from sqlalchemy import text

def setup_ghg_data():
    db = SessionLocal()
    
    try:
        # First, let's check what database we're using
        result = db.execute(text("SELECT version()")).fetchone()
        print(f"Database: {result[0] if result else 'Unknown'}")
        
        # Clear existing data for a clean start
        print("\nClearing existing data...")
        db.query(GHGEmissionFactor).delete()
        db.query(GHGOrganization).delete()
        db.commit()
        
        # Create organization
        print("\nCreating organization...")
        org = GHGOrganization(
            id="12345678-1234-5678-1234-567812345678",
            name="Sample Company",
            industry="Technology",
            country="US"
        )
        db.add(org)
        db.commit()
        print(f"✅ Created organization: {org.name} (ID: {org.id})")
        
        # Create emission factors
        print("\nCreating emission factors...")
        factors = [
            {
                "name": "Purchased Goods - Electronics",
                "category": "purchased_goods_services",
                "factor_value": 2.8,
                "unit": "kg CO2e/USD",
                "source": "EPA",
                "year": 2024,
                "region": "US"
            },
            {
                "name": "Business Travel - Air",
                "category": "business_travel",
                "factor_value": 0.15,
                "unit": "kg CO2e/km",
                "source": "DEFRA",
                "year": 2024,
                "region": "Global"
            },
            {
                "name": "Waste - Landfill",
                "category": "waste_operations",
                "factor_value": 0.467,
                "unit": "kg CO2e/kg",
                "source": "EPA",
                "year": 2024,
                "region": "US"
            },
            {
                "name": "Transport - Road Freight",
                "category": "upstream_transport",
                "factor_value": 0.12,
                "unit": "kg CO2e/ton-km",
                "source": "DEFRA",
                "year": 2024,
                "region": "Global"
            }
        ]
        
        for f in factors:
            factor = GHGEmissionFactor(**f)
            db.add(factor)
        
        db.commit()
        print(f"✅ Created {len(factors)} emission factors")
        
        # Verify data
        print("\nVerifying data...")
        org_count = db.query(GHGOrganization).count()
        factor_count = db.query(GHGEmissionFactor).count()
        print(f"✅ Organizations: {org_count}")
        print(f"✅ Emission factors: {factor_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    setup_ghg_data()
