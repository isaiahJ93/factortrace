#!/usr/bin/env python3
"""Setup GHG data for SQLite with proper UUID handling"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.ghg_tables import GHGOrganization, GHGEmissionFactor
from uuid import uuid4

def setup_ghg_sqlite():
    db = SessionLocal()
    
    try:
        # 1. Create organization with string ID
        org_id = "12345678-1234-5678-1234-567812345678"
        
        existing_org = db.query(GHGOrganization).filter_by(id=org_id).first()
        if not existing_org:
            org = GHGOrganization(
                id=org_id,  # String ID for SQLite
                name="Sample Company",
                industry="Technology",
                country="US"
            )
            db.add(org)
            db.commit()
            print(f"✅ Created organization: {org.name}")
        else:
            print(f"✓ Organization already exists: {existing_org.name}")
        
        # 2. Create emission factors with string IDs
        factor_count = db.query(GHGEmissionFactor).count()
        if factor_count == 0:
            factors = [
                GHGEmissionFactor(
                    id=str(uuid4()),  # Convert UUID to string
                    name="Purchased Goods - General",
                    category="purchased_goods_services",
                    factor_value=2.5,
                    unit="kg CO2e/USD",
                    source="EPA",
                    year=2024,
                    region="US"
                ),
                GHGEmissionFactor(
                    id=str(uuid4()),  # Convert UUID to string
                    name="Business Travel - Air",
                    category="business_travel",
                    factor_value=0.15,
                    unit="kg CO2e/km",
                    source="DEFRA",
                    year=2024,
                    region="Global"
                ),
                GHGEmissionFactor(
                    id=str(uuid4()),  # Convert UUID to string
                    name="Waste - Landfill",
                    category="waste_operations",
                    factor_value=0.467,
                    unit="kg CO2e/kg",
                    source="EPA",
                    year=2024,
                    region="US"
                ),
                GHGEmissionFactor(
                    id=str(uuid4()),  # Convert UUID to string
                    name="Transport - Road Freight",
                    category="upstream_transport",
                    factor_value=0.12,
                    unit="kg CO2e/ton-km",
                    source="DEFRA",
                    year=2024,
                    region="Global"
                )
            ]
            
            for factor in factors:
                db.add(factor)
            
            db.commit()
            print(f"✅ Created {len(factors)} emission factors")
        else:
            print(f"✓ Emission factors already exist: {factor_count}")
        
        print("\n✅ Database is ready for GHG calculations!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_ghg_sqlite()
