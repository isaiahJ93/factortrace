#!/usr/bin/env python3
"""Minimal GHG test"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.ghg_tables import GHGCalculationResult, GHGOrganization
from uuid import uuid4

def test_minimal():
    db = SessionLocal()
    
    try:
        # Check if we can create a calculation record
        print("Testing minimal calculation creation...")
        
        calc_id = str(uuid4())
        org_id = "12345678-1234-5678-1234-567812345678"
        
        print(f"Calc ID: {calc_id} (type: {type(calc_id)})")
        print(f"Org ID: {org_id} (type: {type(org_id)})")
        
        # Check org exists
        org = db.query(GHGOrganization).filter_by(id=org_id).first()
        print(f"Organization exists: {org is not None}")
        
        # Try to create a calculation
        calc = GHGCalculationResult(
            id=calc_id,
            organization_id=org_id,
            reporting_period_start="2024-01-01",
            reporting_period_end="2024-12-31",
            calculation_method="activity_based",
            status="test",
            total_emissions=100.0
        )
        
        db.add(calc)
        db.commit()
        
        print("✅ Successfully created calculation!")
        
        # Query it back
        result = db.query(GHGCalculationResult).filter_by(id=calc_id).first()
        print(f"Retrieved: {result.id} with emissions: {result.total_emissions}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_minimal()
