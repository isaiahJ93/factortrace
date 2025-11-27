#!/usr/bin/env python3
"""
Test the fixed emissions calculator
"""

import asyncio
import sys
sys.path.append('.')

from app.api.v1.endpoints.ghg_calculator import calculate_emissions, CalculateEmissionsRequest

async def test_fixed_calculator():
    """Test with your exact activity data"""
    
    # Your activity data
    emissions_data = [
        {"activity_type": "natural_gas", "amount": 2343, "unit": "kWh"},
        {"activity_type": "diesel", "amount": 34323, "unit": "litres"},  # Generators
        {"activity_type": "diesel_fleet", "amount": 34212, "unit": "litres"},
        {"activity_type": "petrol", "amount": 23121, "unit": "litres"},
        {"activity_type": "electricity", "amount": 2341, "unit": "kWh"},
    ]
    
    request = CalculateEmissionsRequest(
        company_id="test",
        reporting_period="2025",
        emissions_data=emissions_data
    )
    
    print("🧪 Testing Fixed Emissions Calculator")
    print("=" * 50)
    
    response = await calculate_emissions(request)
    
    print(f"\n📊 Results:")
    print(f"Scope 1: {response.scope1_emissions/1000:.2f} tCO2e")
    print(f"Scope 2: {response.scope2_emissions/1000:.2f} tCO2e")
    print(f"Scope 3: {response.scope3_emissions/1000:.2f} tCO2e")
    print(f"TOTAL: {response.total_emissions_tons_co2e:.2f} tCO2e")
    
    if hasattr(response, 'scope3_detailed'):
        cat3 = response.scope3_detailed.get('category_3', {})
        print(f"\n✨ Category 3 (Fuel & Energy): {cat3.get('emissions_tco2e', 0):.2f} tCO2e")
        
        expected_cat3 = 56.2
        actual_cat3 = cat3.get('emissions_tco2e', 0)
        
        if abs(actual_cat3 - expected_cat3) < 1:
            print("✅ Category 3 calculating correctly!")
        else:
            print(f"❌ Category 3 mismatch: Expected ~{expected_cat3}, got {actual_cat3}")
    
    print(f"\n📈 Breakdown:")
    for item in response.breakdown:
        print(f"  {item.activity_type}: {item.emissions_kg_co2e/1000:.2f} tCO2e")

if __name__ == "__main__":
    asyncio.run(test_fixed_calculator())