#!/usr/bin/env python3
"""Debug GHG calculation error"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from app.core.database import SessionLocal
from app.services.ghg_calculation_service import GHGCalculationService
from app.schemas.ghg_schemas import CalculationRequest, ActivityDataInput, Scope3Category, CalculationMethod
import traceback

async def debug_calculation():
    db = SessionLocal()
    
    try:
        print("=== DEBUGGING GHG CALCULATION ===\n")
        
        # First check if organization exists
        from app.models.ghg_tables import GHGOrganization, GHGEmissionFactor
        
        org = db.query(GHGOrganization).filter_by(id="12345678-1234-5678-1234-567812345678").first()
        print(f"✓ Organization exists: {org is not None}")
        if org:
            print(f"  - Name: {org.name}")
            print(f"  - ID: {org.id}")
            print(f"  - Type: {type(org.id)}")
        
        # Check emission factors
        factors = db.query(GHGEmissionFactor).all()
        print(f"\n✓ Emission factors: {len(factors)}")
        
        # Create request
        print("\n📝 Creating calculation request...")
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
        
        # Try to create calculation
        print("\n🚀 Calling calculation service...")
        service = GHGCalculationService(db)
        
        # Add some debug prints
        print(f"  - Organization ID type in request: {type(request.organization_id)}")
        print(f"  - Organization ID value: {request.organization_id}")
        
        result = await service.create_calculation(request)
        
        print(f"\n✅ SUCCESS! Calculation ID: {result.calculation_id}")
        print(f"Total emissions: {result.total_emissions} kg CO2e")
        
    except Exception as e:
        print(f"\n❌ ERROR FOUND!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\n🔍 FULL TRACEBACK:")
        print("-" * 60)
        traceback.print_exc()
        print("-" * 60)
        
        # Additional debugging
        if "foreign key" in str(e).lower():
            print("\n⚠️  This is a foreign key error!")
            print("Checking organization again...")
            org = db.query(GHGOrganization).filter_by(id="12345678-1234-5678-1234-567812345678").first()
            print(f"Organization in DB: {org is not None}")
            
            if org:
                print(f"Org ID: {org.id} (type: {type(org.id)})")
                print(f"String comparison: {str(org.id) == '12345678-1234-5678-1234-567812345678'}")
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_calculation())
