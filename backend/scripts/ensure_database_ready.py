#!/usr/bin/env python3
"""Ensure database is ready for GHG calculations"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.ghg_tables import GHGOrganization, GHGEmissionFactor
from app.core.config import settings

def ensure_database_ready():
    db = SessionLocal()
    
    print(f"Using database: {settings.DATABASE_URL}")
    
    try:
        # Ensure organization exists
        org_id = "12345678-1234-5678-1234-567812345678"
        org = db.query(GHGOrganization).filter_by(id=org_id).first()
        
        if not org:
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
            print(f"✓ Organization exists: {org.name}")
        
        # Ensure emission factors exist
        factors = db.query(GHGEmissionFactor).count()
        if factors == 0:
            factor_data = [
                {
                    "name": "Purchased Goods - General",
                    "category": "purchased_goods_services", 
                    "factor_value": 2.5,
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
                }
            ]
            
            for data in factor_data:
                factor = GHGEmissionFactor(**data)
                db.add(factor)
            
            db.commit()
            print(f"✅ Created {len(factor_data)} emission factors")
        else:
            print(f"✓ Emission factors exist: {factors}")
        
        print("\n✅ Database is ready for GHG calculations!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    ensure_database_ready()
