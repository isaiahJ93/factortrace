#!/usr/bin/env python3
"""Test GHG calculation directly"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.ghg_tables import GHGEmissionFactor, GHGOrganization
from app.services.ghg_calculation_service import GHGCalculationService
from app.schemas.ghg_schemas import CalculationRequest, ActivityDataInput, Scope3Category
from app.core.config import settings
from datetime import datetime
import uuid

async def test_calculation():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Create test request
    request = CalculationRequest(
        organization_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        reporting_period_start=datetime(2024, 1, 1),
        reporting_period_end=datetime(2024, 12, 31),
        activity_data=[
            ActivityDataInput(
                category=Scope3Category.PURCHASED_GOODS,
                activity_type="Electronics",
                amount=100000,
                unit="USD"
            ),
            ActivityDataInput(
                category=Scope3Category.BUSINESS_TRAVEL,
                activity_type="Air Travel",
                amount=50000,
                unit="km"
            )
        ]
    )
    
    # Create service and calculate
    service = GHGCalculationService(db)
    try:
        result = await service.create_calculation(request)
        print(f"✅ Calculation successful!")
        print(f"Total emissions: {result.total_emissions} kg CO2e")
        print(f"Calculation ID: {result.calculation_id}")
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_calculation())
