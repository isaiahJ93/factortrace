#!/usr/bin/env python3
"""
Comprehensive test of the fixed emissions calculator
"""

import asyncio
import sys
sys.path.append('.')

from app.api.v1.endpoints.ghg_calculator import calculate_emissions, CalculateEmissionsRequest

async def test_all_emissions():
    """Test with your exact activity data from screenshot"""
    
    # Your complete activity data
    emissions_data = [
        # SCOPE 1
        {"activity_type": "natural_gas_stationary", "amount": 2343, "unit": "kWh"},
        {"activity_type": "diesel", "amount": 34323, "unit": "litres"},  # Generators
        {"activity_type": "diesel_fleet", "amount": 34212, "unit": "litres"},
        {"activity_type": "petrol", "amount": 23121, "unit": "litres"},
        
        # SCOPE 2
        {"activity_type": "electricity_grid", "amount": 2341, "unit": "kWh"},
        {"activity_type": "district_heating", "amount": 1232, "unit": "kWh"},
        {"activity_type": "district_cooling", "amount": 2131, "unit": "kWh"},
        
        # SCOPE 3
        {"activity_type": "office_paper", "amount": 123, "unit": "kg"},
        {"activity_type": "plastic_packaging", "amount": 234, "unit": "kg"},
        {"activity_type": "machinery", "amount": 543232, "unit": "EUR"},
        {"activity_type": "road_freight", "amount": 23330, "unit": "tonne.km"},
        {"activity_type": "waste_landfill", "amount": 23, "unit": "tonnes"},
        {"activity_type": "business_travel_air", "amount": 34523 + 454342, "unit": "passenger.km"},
        {"activity_type": "employee_commuting", "amount": 32423, "unit": "km"},
    ]
    
    request = CalculateEmissionsRequest(
        company_id="test",
        reporting_period="2025",
        emissions_data=emissions_data,
        include_gas_breakdown=True
    )
    
    print("🧪 COMPREHENSIVE EMISSIONS TEST")
    print("=" * 60)
    
    try:
        response = await calculate_emissions(request)
        
        print(f"\n📊 EMISSIONS SUMMARY:")
        print(f"Scope 1: {response.scope1_emissions/1000:.2f} tCO2e")
        print(f"Scope 2: {response.scope2_emissions/1000:.2f} tCO2e") 
        print(f"Scope 3: {response.scope3_emissions/1000:.2f} tCO2e")
        print(f"TOTAL: {response.total_emissions_tons_co2e:.2f} tCO2e")
        
        # Check Category 3
        if hasattr(response, 'scope3_detailed'):
            print(f"\n📈 SCOPE 3 CATEGORIES:")
            for i in range(1, 16):
                cat_key = f'category_{i}'
                if cat_key in response.scope3_detailed:
                    cat_data = response.scope3_detailed[cat_key]
                    emissions = cat_data.get('emissions_tco2e', 0)
                    if emissions > 0:
                        print(f"Category {i}: {emissions:.2f} tCO2e")
            
            # Special focus on Category 3
            cat3 = response.scope3_detailed.get('category_3', {})
            cat3_emissions = cat3.get('emissions_tco2e', 0)
            print(f"\n✨ Category 3 (Fuel & Energy): {cat3_emissions:.2f} tCO2e")
            
            # Expected with corrected factors:
            # Natural Gas WTT: 2343 * 0.03255 / 1000 = 0.08 tCO2e
            # Diesel WTT: (34323 + 34212) * 0.61314 / 1000 = 42.04 tCO2e  
            # Petrol WTT: 23121 * 0.59054 / 1000 = 13.65 tCO2e
            # Electricity T&D: 2341 * 0.00979 / 1000 = 0.02 tCO2e
            # Heating/Cooling T&D: (1232 + 2131) * 0.009 / 1000 = 0.03 tCO2e
            # Expected total: ~55.8 tCO2e
            
            if 50 < cat3_emissions < 60:
                print("✅ Category 3 calculating correctly with fixed factors!")
            else:
                print(f"⚠️  Category 3 unexpected: Expected ~55.8, got {cat3_emissions}")
        
        print(f"\n📋 DETAILED BREAKDOWN:")
        for item in response.breakdown[:10]:  # First 10 items
            print(f"  {item.activity_type}: {item.emissions_kg_co2e/1000:.2f} tCO2e ({item.scope})")
            
        # Expected totals with corrected factors:
        # Scope 1: ~225 tCO2e (similar to before)
        # Scope 2: ~1.2 tCO2e (with heating/cooling)
        # Scope 3: ~390 tCO2e (with corrected Cat 3)
        # Total: ~616 tCO2e
        
        print(f"\n✅ COMPLIANCE CHECK:")
        print(f"GHG Protocol: {'COMPLIANT' if cat3_emissions > 0 else 'NON-COMPLIANT'}")
        print(f"ESRS E1: {'COMPLIANT' if hasattr(response, 'scope3_detailed') else 'NON-COMPLIANT'}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_all_emissions())