#!/usr/bin/env python3
"""Create a test calculation directly"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.ghg_tables import GHGCalculationResult, GHGOrganization, GHGEmissionFactor
from uuid import uuid4
from datetime import datetime

db = SessionLocal()

try:
    # Create a test calculation
    calc_id = str(uuid4())
    org_id = "12345678-1234-5678-1234-567812345678"
    
    # Verify org exists
    org = db.query(GHGOrganization).filter_by(id=org_id).first()
    if not org:
        print("❌ Organization not found! Run setup_ghg_sqlite.py first")
        exit(1)
    
    calc = GHGCalculationResult(
        id=calc_id,
        organization_id=org_id,
        reporting_period_start=datetime(2024, 1, 1),
        reporting_period_end=datetime(2024, 12, 31),
        total_emissions=12345.67,
        calculation_method="activity_based",
        status="completed",
        uncertainty_min=11111.11,
        uncertainty_max=13579.99,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    
    db.add(calc)
    db.commit()
    
    print(f"✅ Created test calculation!")
    print(f"   ID: {calc_id}")
    print(f"   Emissions: {calc.total_emissions} kg CO2e")
    print(f"\n📋 Use this to test GET endpoint:")
    print(f"   curl http://localhost:8000/api/v1/ghg/calculations/{calc_id} | jq .")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
