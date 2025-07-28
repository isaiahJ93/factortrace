#!/usr/bin/env python3
"""Complete GHG debugging"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.ghg_tables import GHGOrganization, GHGEmissionFactor, GHGCalculationResult
from app.core.config import settings
from sqlalchemy import text

def debug_complete():
    db = SessionLocal()
    
    print("=== GHG SYSTEM DEBUGGING ===\n")
    
    # 1. Database info
    print(f"1. DATABASE INFO:")
    print(f"   URL: {settings.DATABASE_URL}")
    
    # Check if PostgreSQL or SQLite
    if 'postgresql' in str(engine.url):
        result = db.execute(text("SELECT current_database(), version()")).first()
        print(f"   Type: PostgreSQL")
        print(f"   Database: {result[0]}")
        print(f"   Version: {result[1][:30]}...")
    else:
        result = db.execute(text("SELECT sqlite_version()")).scalar()
        print(f"   Type: SQLite")
        print(f"   Version: {result}")
    
    # 2. Check tables
    print(f"\n2. TABLES:")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    ghg_tables = [t for t in tables if 'ghg_' in t]
    print(f"   GHG tables: {', '.join(ghg_tables)}")
    
    # 3. Check organization
    print(f"\n3. ORGANIZATION:")
    org_id = "12345678-1234-5678-1234-567812345678"
    org = db.query(GHGOrganization).filter_by(id=org_id).first()
    if org:
        print(f"   ✓ Found: {org.name}")
        print(f"   ID: {org.id} (type: {type(org.id)})")
    else:
        print(f"   ✗ NOT FOUND for ID: {org_id}")
        
        # Try to create it
        print("   Attempting to create...")
        try:
            new_org = GHGOrganization(
                id=org_id,
                name="Sample Company",
                industry="Technology",
                country="US"
            )
            db.add(new_org)
            db.commit()
            print("   ✓ Created successfully!")
        except Exception as e:
            print(f"   ✗ Failed to create: {e}")
            db.rollback()
    
    # 4. Check emission factors
    print(f"\n4. EMISSION FACTORS:")
    factors = db.query(GHGEmissionFactor).all()
    print(f"   Total: {len(factors)}")
    for f in factors[:3]:
        print(f"   - {f.name}: {f.factor_value} {f.unit}")
    
    # 5. Check calculations
    print(f"\n5. CALCULATIONS:")
    calcs = db.query(GHGCalculationResult).all()
    print(f"   Total: {len(calcs)}")
    for c in calcs[:3]:
        print(f"   - ID: {c.id}")
        print(f"     Org: {c.organization_id}")
        print(f"     Emissions: {c.total_emissions}")
    
    # 6. Test minimal insert
    print(f"\n6. TEST CALCULATION INSERT:")
    try:
        from uuid import uuid4
        test_id = str(uuid4())
        test_calc = GHGCalculationResult(
            id=test_id,
            organization_id=org_id,
            reporting_period_start="2024-01-01",
            reporting_period_end="2024-12-31",
            calculation_method="activity_based",
            status="test",
            total_emissions=123.45
        )
        db.add(test_calc)
        db.commit()
        print(f"   ✓ Test insert successful! ID: {test_id}")
        
        # Clean up
        db.query(GHGCalculationResult).filter_by(id=test_id).delete()
        db.commit()
        print(f"   ✓ Cleaned up test record")
        
    except Exception as e:
        print(f"   ✗ Test insert failed: {e}")
        db.rollback()
    
    db.close()
    print("\n=== DEBUGGING COMPLETE ===")

if __name__ == "__main__":
    debug_complete()
