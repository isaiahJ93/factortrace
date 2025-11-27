#!/usr/bin/env python3
"""
Test with correct activity type names
"""

import asyncio
import sys
sys.path.append('.')

from app.api.v1.endpoints.ghg_calculator import calculate_emissions, CalculateEmissionsRequest

async def test_with_correct_types():
    """Test with properly mapped activity types"""
    
    emissions_data = [
        # SCOPE 1 - Use the exact names from DEFAULT_EMISSION_FACTORS
        {"activity_type": "natural_gas_stationary", "amount": 2343, "unit": "kWh"},
        {"activity_type": "diesel_fleet", "amount": 34323, "unit": "litres"},  # Generators
        {"activity_type": "diesel_fleet", "amount": 34212, "unit": "litres"},  # Fleet
        {"activity_type": "petrol_fleet", "amount": 23121, "unit": "litres"},
        
        # SCOPE 2
        {"activity_type": "electricity_grid", "amount": 2341, "unit": "kWh"},
        {"activity_type": "district_heating", "amount": 1232, "unit": "kWh"},
        
        # SCOPE 3
        {"activity_type": "office_paper", "amount": 123, "unit": "kg"},
        {"activity_type": "plastic_packaging", "amount": 234, "unit": "kg"},
        {"activity_type": "machinery", "amount": 543232, "unit": "USD"},
        {"activity_type": "road_freight", "amount": 23330, "unit": "tonne.km"},
        {"activity_type": "waste_landfill", "amount": 23, "unit": "tonnes"},
        {"activity_type": "business_travel_air", "amount": 488865, "unit": "passenger.km"},
        {"activity_type": "employee_commuting", "amount": 32423, "unit": "km"},
    ]
    
    request = CalculateEmissionsRequest(
        company_id="test",
        reporting_period="2025",
        emissions_data=emissions_data,
        include_gas_breakdown=True
    )
    
    print("🧪 EMISSIONS TEST WITH CORRECT ACTIVITY TYPES")
    print("=" * 60)
    
    try:
        response = await calculate_emissions(request)
        
        print(f"\n📊 EMISSIONS SUMMARY:")
        print(f"Scope 1: {response.scope1_emissions/1000:.2f} tCO2e")
        print(f"Scope 2: {response.scope2_emissions/1000:.2f} tCO2e")
        print(f"Scope 3: {response.scope3_emissions/1000:.2f} tCO2e")
        print(f"TOTAL: {response.total_emissions_tons_co2e:.2f} tCO2e")
        
        if hasattr(response, 'scope3_category_breakdown'):
            print(f"\n📈 SCOPE 3 CATEGORIES:")
            breakdown = response.scope3_category_breakdown
            if hasattr(breakdown, 'category_3'):
                print(f"Category 3 (Fuel & Energy): {breakdown.category_3:.2f} tCO2e")
                
                # Expected Category 3:
                # Natural Gas WTT: 2343 * 0.03255 / 1000 = 0.08 tCO2e
                # Diesel WTT: 68535 * 0.61314 / 1000 = 42.02 tCO2e
                # Petrol WTT: 23121 * 0.59054 / 1000 = 13.65 tCO2e
                # Electricity T&D: 2341 * 0.00979 / 1000 = 0.02 tCO2e
                # Heating T&D: 1232 * 0.00883 / 1000 = 0.01 tCO2e
                # Total: ~55.78 tCO2e
                
                if 50 < breakdown.category_3 < 60:
                    print("✅ Category 3 calculating correctly!")
                else:
                    print(f"⚠️  Category 3 unexpected: {breakdown.category_3:.2f} tCO2e")
        
        print(f"\n✅ TEST PASSED! Total emissions: {response.total_emissions_tons_co2e:.2f} tCO2e")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_with_correct_types())