#!/usr/bin/env python3
"""Test with detailed logging"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.DEBUG)

from app.core.database import SessionLocal
from app.services.ghg_calculation_service import GHGCalculationService
from app.schemas.ghg_schemas import CalculationRequest, ActivityDataInput, Scope3Category, CalculationMethod
from datetime import datetime
import asyncio

async def test_with_logging():
    db = SessionLocal()
    
    try:
        request = CalculationRequest(
            organization_id="12345678-1234-5678-1234-567812345678",
            reporting_period_start=datetime(2024, 1, 1),
            reporting_period_end=datetime(2024, 12, 31),
            activity_data=[
                ActivityDataInput(
                    category=Scope3Category.PURCHASED_GOODS,
                    activity_type="Test",
                    amount=1000.0,
                    unit="USD"
                )
            ],
            calculation_method=CalculationMethod.ACTIVITY_BASED,
            include_uncertainty=False
        )
        
        service = GHGCalculationService(db)
        print("Starting calculation...")
        result = await service.create_calculation(request)
        print(f"✅ Success! ID: {result.calculation_id}")
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

asyncio.run(test_with_logging())
