import requests
import json
from datetime import date

# Backend URL
BASE_URL = "http://localhost:8000/api/v1"

def test_ghg_calculator():
    """Test the GHG calculator endpoint"""
    
    # Test data
    test_request = {
        "company_id": "test-company",
        "reporting_period": "2024-Q1",
        "emissions_data": [
            {"activity_type": "electricity", "amount": 1000, "unit": "kWh"},
            {"activity_type": "natural_gas", "amount": 500, "unit": "m3"},
            {"activity_type": "vehicle_fuel", "amount": 200, "unit": "liters"},
            {"activity_type": "business_travel", "amount": 5000, "unit": "km"}
        ]
    }
    
    print("🧪 Testing GHG Calculator API...")
    print(f"📡 Sending request to {BASE_URL}/ghg-calculator/calculate")
    print(f"📊 Test data: {json.dumps(test_request, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(
            f"{BASE_URL}/ghg-calculator/calculate",
            json=test_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success! Calculation results:")
            print(f"   Total emissions: {result['total_emissions_tons_co2e']} tCO2e")
            print(f"   Scope 1: {result['scope1_emissions']/1000:.2f} tCO2e")
            print(f"   Scope 2: {result['scope2_emissions']/1000:.2f} tCO2e")
            print(f"   Scope 3: {result['scope3_emissions']/1000:.2f} tCO2e")
            print("\n📋 Breakdown by activity:")
            for item in result['breakdown']:
                print(f"   - {item['activity_type']}: {item['emissions_kg_co2e']} kg CO2e ({item['scope']})")
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to backend!")
        print("   Make sure the backend is running on http://localhost:8000")
        print("   Run: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

def test_activity_types():
    """Test getting activity types"""
    print("\n🧪 Testing activity types endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/ghg-calculator/activity-types")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Available activity types:")
            for scope, activities in result.items():
                print(f"\n   {scope.upper()}:")
                for activity in activities:
                    print(f"   - {activity['label']} ({activity['value']}) - Unit: {activity['unit']}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 GHG Calculator API Test\n")
    test_ghg_calculator()
    test_activity_types()
    print("\n✨ Test complete!")