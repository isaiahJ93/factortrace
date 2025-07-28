# test_monte_carlo_features.py - Test if Monte Carlo is accessible in your API
"""
Test script to check if Monte Carlo uncertainty features are available
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def find_api_endpoints():
    """Discover available endpoints"""
    print("🔍 Discovering API endpoints...\n")
    
    # Try to get OpenAPI schema
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            print("📋 Available endpoints:")
            for path, methods in openapi.get("paths", {}).items():
                for method in methods:
                    print(f"  {method.upper()} {path}")
            print()
    except:
        print("Could not fetch OpenAPI schema")
    
    # Try common endpoints
    test_endpoints = [
        "/api/v1/ghg/calculate",
        "/api/v1/ghg-calculations/calculate",
        "/api/v1/emissions/calculate",
        "/api/v1/calculations",
        "/api/v1/ghg-calculator/calculate",  # Your simple API
    ]
    
    print("🧪 Testing known endpoints:")
    for endpoint in test_endpoints:
        try:
            response = requests.options(endpoint)
            if response.status_code < 500:
                print(f"  ✅ {endpoint} exists")
        except:
            pass

def test_calculation_with_uncertainty():
    """Test calculation with uncertainty parameters"""
    print("\n🎲 Testing Monte Carlo uncertainty features...\n")
    
    # Test data with uncertainty parameters
    test_data = {
        "company_id": "test-company",
        "reporting_year": 2024,
        "reporting_period": "2024-Q1",
        "activity_data": [
            {
                "activity_type": "electricity",
                "quantity": 10000,
                "unit": "kWh",
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "data_quality": "primary",
                "uncertainty_percentage": 5.0
            },
            {
                "activity_type": "natural_gas", 
                "quantity": 5000,
                "unit": "m3",
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "data_quality": "estimated",
                "uncertainty_percentage": 20.0
            }
        ],
        "emissions_data": [  # Alternative format
            {
                "activity_type": "electricity",
                "amount": 10000,
                "unit": "kWh",
                "uncertainty_percentage": 5.0
            }
        ],
        "calculation_method": "activity_based",
        "include_uncertainty": True,
        "monte_carlo_runs": 1000
    }
    
    # Try different endpoint patterns
    endpoints_to_try = [
        ("/api/v1/ghg-calculations/calculate", test_data),
        ("/api/v1/ghg/calculate", test_data),
        ("/api/v1/emissions/calculate", test_data),
        ("/api/v1/ghg-calculator/calculate", {  # Your simple API format
            "reporting_period": "2024-Q1",
            "emissions_data": test_data["emissions_data"]
        })
    ]
    
    for endpoint, data in endpoints_to_try:
        print(f"📡 Testing {endpoint}...")
        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                
                # Check for uncertainty fields
                has_monte_carlo = any([
                    "uncertainty" in str(result),
                    "confidence_interval" in str(result),
                    "monte_carlo" in str(result),
                    "uncertainty_analysis" in str(result),
                    "uncertainty_range" in str(result)
                ])
                
                if has_monte_carlo:
                    print("🎉 Monte Carlo uncertainty features ARE ACTIVE!")
                    print("\nUncertainty fields found:")
                    for key in result:
                        if "uncertainty" in key.lower() or "confidence" in key.lower():
                            print(f"  - {key}: {result[key]}")
                else:
                    print("❌ No uncertainty features in response")
                
                # Show the response structure
                print(f"\nResponse structure: {list(result.keys())}")
                
                # Check for scope 2 dual reporting
                if "scope2_location_based" in result or "scope2_market_based" in result:
                    print("✅ Dual Scope 2 reporting is active!")
                
                return result
                
            elif response.status_code == 422:
                print(f"❌ Validation error: {response.json()}")
            else:
                print(f"❌ Error {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
    
    return None

def check_ghg_service_endpoints():
    """Check if full GHG service endpoints are available"""
    print("\n🔍 Checking for full GHG service endpoints...\n")
    
    # These would be from your full API
    service_endpoints = [
        "/api/v1/emission-factors",
        "/api/v1/ghg-protocols",
        "/api/v1/activity-data",
        "/api/v1/calculations/monte-carlo",
        "/api/v1/reports/uncertainty"
    ]
    
    for endpoint in service_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code < 500:
                print(f"✅ {endpoint} - Status: {response.status_code}")
        except:
            pass

if __name__ == "__main__":
    print("🧪 GHG API Monte Carlo Feature Test\n")
    
    # Check what's running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print(f"✅ API is running at {BASE_URL}")
            api_info = response.json()
            if "message" in api_info:
                print(f"   API: {api_info['message']}")
        print()
    except:
        print(f"❌ No API running at {BASE_URL}")
        print("   Please start your API first!")
        exit(1)
    
    # Run tests
    find_api_endpoints()
    result = test_calculation_with_uncertainty()
    check_ghg_service_endpoints()
    
    # Summary
    print("\n" + "="*50)
    print("📊 SUMMARY:")
    if result and any("uncertainty" in k for k in str(result)):
        print("✅ Monte Carlo uncertainty calculations are ACTIVE!")
        print("✅ Your sophisticated GHG features are working!")
    else:
        print("❌ Monte Carlo features not found in API responses")
        print("💡 You may be running the simple API instead of your full-featured one")
        print("\nTo use your full features, run:")
        print("  uvicorn app.main:app --reload")
        print("\nInstead of:")
        print("  python run_ghg_api.py")