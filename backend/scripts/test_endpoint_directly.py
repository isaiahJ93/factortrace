#!/usr/bin/env python3
"""Test endpoint directly"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.v1.endpoints.ghg_calculations import create_calculation
from app.schemas.ghg_schemas import CalculationRequest, ActivityDataInput, Scope3Category, CalculationMethod
from app.core.database import SessionLocal
from datetime import datetime
import asyncio

async def test_endpoint():
    db = SessionLocal()
    
    try:
        request = CalculationRequest(
            organization_id="12345678-1234-5678-1234-567812345678",
            reporting_period_start=datetime(2024, 1, 1),
            reporting_period_end=datetime(2024, 12, 31),
            activity_data=[
                ActivityDataInput(
                    category=Scope3Category.PURCHASED_GOODS,
                    activity_type="Electronics",
                    amount=100000.0,
                    unit="USD"
                )
            ],
            calculation_method=CalculationMethod.ACTIVITY_BASED,
            include_uncertainty=True
        )
        
        # Mock the Depends
        class MockBackgroundTasks:
            def add_task(self, *args, **kwargs):
                pass
        
        result = await create_calculation(request, db, MockBackgroundTasks())
        print(f"✅ Success! Result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
