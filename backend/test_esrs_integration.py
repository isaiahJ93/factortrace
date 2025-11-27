#!/usr/bin/env python3
"""
Test GHG Calculator directly with your data
"""

import asyncio
import json
from datetime import datetime
import sys
sys.path.append('.')

async def test_ghg_calculator():
    """Test the GHG calculator with your activity data"""
    
    from app.api.v1.endpoints.ghg_calculator import calculate_emissions, CalculateEmissionsRequest
    
    # Your activity data converted to emissions format
    emissions_data = [
        {"activity_type": "natural_gas", "amount": 2343, "unit": "kWh"},
        {"activity_type": "diesel", "amount": 34323, "unit": "litres"},  # Generators
        {"activity_type": "diesel_fleet", "amount": 34212, "unit": "litres"},
        {"activity_type": "petrol", "amount": 23121, "unit": "litres"},
        {"activity_type": "electricity", "amount": 2341, "unit": "kWh"},
        {"activity_type": "office_paper", "amount": 23, "unit": "kg"},
        {"activity_type": "plastic_packaging", "amount": 234393, "unit": "kg"},
        {"activity_type": "road_freight", "amount": 23330, "unit": "tonne.km"},
        {"activity_type": "waste_landfill", "amount": 23, "unit": "tonnes"},
        {"activity_type": "business_travel_air", "amount": 34523 + 454342, "unit": "passenger.km"},
        {"activity_type": "machinery", "amount": 543232, "unit": "EUR"},
        {"activity_type": "buildings", "amount": 234323, "unit": "EUR"},
        {"activity_type": "employee_commuting", "amount": 32423, "unit": "passenger.km"}
    ]
    
    request = CalculateEmissionsRequest(
        company_id="test",
        reporting_period="2025",
        emissions_data=emissions_data,
        include_gas_breakdown=True
    )
    
    try:
        print("🚀 Testing GHG Calculator directly...")
        response = await calculate_emissions(request)
        
        print(f"\n📊 Emission Results:")
        print(f"   Scope 1: {response.scope1_emissions:,.2f} kg CO2e ({response.scope1_emissions/1000:.2f} tCO2e)")
        print(f"   Scope 2: {response.scope2_emissions:,.2f} kg CO2e ({response.scope2_emissions/1000:.2f} tCO2e)")
        print(f"   Scope 3: {response.scope3_emissions:,.2f} kg CO2e ({response.scope3_emissions/1000:.2f} tCO2e)")
        print(f"   TOTAL: {response.total_emissions_tons_co2e:.2f} tCO2e")
        
        if hasattr(response, 'scope3_detailed') and response.scope3_detailed:
            print(f"\n📈 Scope 3 Categories:")
            cat3 = response.scope3_detailed.get('category_3', {})
            print(f"   Category 3 (Fuel & Energy): {cat3.get('emissions_tco2e', 0):.2f} tCO2e")
            
            # Show all categories with emissions
            for i in range(1, 16):
                cat_data = response.scope3_detailed.get(f'category_{i}', {})
                emissions = cat_data.get('emissions_tco2e', 0)
                if emissions > 0:
                    print(f"   Category {i}: {emissions:.2f} tCO2e")
        
        print(f"\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ghg_calculator())