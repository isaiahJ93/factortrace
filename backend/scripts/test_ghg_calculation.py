#!/usr/bin/env python3
"""Test GHG calculation with detailed error reporting"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import traceback
from datetime import datetime
from app.core.database import SessionLocal
from app.services.ghg_calculation_service import GHGCalculationService
from app.schemas.ghg_schemas import CalculationRequest, ActivityDataInput, Scope3Category, CalculationMethod

async def test_calculation():
    db = SessionLocal()
    
    try:
        # Create test request
        request = CalculationRequest(
            organization_id="12345678-1234-5678-1234-567812345678",
            reporting_period_start=datetime(2024, 1, 1),
            reporting_period_end=datetime(2024, 12, 31),
            activity_data=[
                ActivityDataInput(
                    category=Scope3Category.PURCHASED_GOODS,
                    activity_type="Electronics",
                    amount=100000.0,
                    unit="USD",
                    description="IT Equipment"
                )
            ],
            calculation_method=CalculationMethod.ACTIVITY_BASED,
            include_uncertainty=True
        )
        
        print(f"Request created: {request}")
        
        # Create service and calculate
        service = GHGCalculationService(db)
        result = await service.create_calculation(request)
        
        print(f"\n✅ Calculation successful!")
        print(f"Calculation ID: {result.calculation_id}")
        print(f"Total emissions: {result.total_emissions} kg CO2e")
        print(f"Status: {result.status}")
        
        # Pretty print the results
        print("\nCategory Results:")
        for cat_result in result.category_results:
            print(f"  - {cat_result.category}: {cat_result.emissions_co2e} kg CO2e")
        
        if result.uncertainty_analysis:
            print(f"\nUncertainty Analysis:")
            print(f"  - Mean: {result.uncertainty_analysis['mean']:.2f}")
            print(f"  - 95% confidence: {result.uncertainty_analysis['percentiles']['5']:.2f} - {result.uncertainty_analysis['percentiles']['95']:.2f}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    result = asyncio.run(test_calculation())
    if result:
        print(f"\n📊 Use this ID to test GET: {result.calculation_id}")
