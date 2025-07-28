# backend/test_emissions_api.py
"""
Test script to verify the emissions API is working correctly
Run this after setting up the database
"""
import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_health_check():
    """Test the health endpoint"""
    print("🔍 Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    return response.status_code == 200

def test_get_emissions_summary():
    """Test getting emissions summary"""
    print("\n🔍 Testing GET /emissions/summary...")
    response = requests.get(f"{BASE_URL}/emissions/summary")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Scope 1 Total: {data.get('scope1_total', 0)} tCO2e")
        print(f"  Scope 2 Total: {data.get('scope2_total', 0)} tCO2e")
        print(f"  Scope 3 Total: {data.get('scope3_total', 0)} tCO2e")
        print(f"  Total Emissions: {data.get('total_emissions', 0)} tCO2e")
    return response.status_code == 200

def test_create_emission():
    """Test creating a new emission"""
    print("\n🔍 Testing POST /emissions...")
    
    # Test data
    emission_data = {
        "scope": 3,
        "category": "purchased_goods",
        "activity_data": 100.0,
        "unit": "kg",
        "emission_factor": 2.5,
        "data_source": "calculated",
        "location": "Test Location",
        "description": "Test emission from API test script"
    }
    
    response = requests.post(
        f"{BASE_URL}/emissions",
        json=emission_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"  Status: {response.status_code}")
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"  Created Emission ID: {data.get('id')}")
        print(f"  Amount: {data.get('amount')} tCO2e")
        return True, data.get('id')
    else:
        print(f"  Error: {response.text}")
        return False, None

def test_get_emissions():
    """Test getting all emissions"""
    print("\n🔍 Testing GET /emissions...")
    response = requests.get(f"{BASE_URL}/emissions")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Number of emissions: {len(data)}")
        if data:
            print("  First emission:")
            print(f"    - ID: {data[0].get('id')}")
            print(f"    - Scope: {data[0].get('scope')}")
            print(f"    - Category: {data[0].get('category')}")
            print(f"    - Amount: {data[0].get('amount')} tCO2e")
    return response.status_code == 200

def test_update_emission(emission_id):
    """Test updating an emission"""
    print(f"\n🔍 Testing PUT /emissions/{emission_id}...")
    
    update_data = {
        "description": "Updated description from test script",
        "location": "Updated Location"
    }
    
    response = requests.put(
        f"{BASE_URL}/emissions/{emission_id}",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Updated Description: {data.get('description')}")
        print(f"  Updated Location: {data.get('location')}")
    return response.status_code == 200

def test_delete_emission(emission_id):
    """Test deleting an emission"""
    print(f"\n🔍 Testing DELETE /emissions/{emission_id}...")
    
    response = requests.delete(f"{BASE_URL}/emissions/{emission_id}")
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Message: {response.json().get('message')}")
    return response.status_code == 200

def test_calculate_endpoint():
    """Test the calculate endpoint"""
    print("\n🔍 Testing POST /emissions/calculate...")
    
    calc_data = {
        "activity_data": 1000,
        "emission_factor": 0.5,
        "unit": "kg"
    }
    
    response = requests.post(
        f"{BASE_URL}/emissions/calculate",
        json=calc_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Calculated Emissions: {data.get('calculated_emissions')} {data.get('unit')}")
    return response.status_code == 200

def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Emissions API Tests")
    print("=" * 50)
    
    results = []
    
    # Test health check
    results.append(("Health Check", test_health_check()))
    
    # Test emissions summary
    results.append(("Get Summary", test_get_emissions_summary()))
    
    # Test creating emission
    success, emission_id = test_create_emission()
    results.append(("Create Emission", success))
    
    # Test getting emissions
    results.append(("Get Emissions", test_get_emissions()))
    
    # If emission was created, test update and delete
    if emission_id:
        results.append(("Update Emission", test_update_emission(emission_id)))
        results.append(("Delete Emission", test_delete_emission(emission_id)))
    
    # Test calculate endpoint
    results.append(("Calculate Emissions", test_calculate_endpoint()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your emissions API is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    run_all_tests()