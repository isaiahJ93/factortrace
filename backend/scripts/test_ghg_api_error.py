#!/usr/bin/env python3
"""Test GHG API and capture exact error"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json

def test_api_error():
    url = "http://localhost:8000/api/v1/ghg/calculations/"
    
    data = {
        "organization_id": "12345678-1234-5678-1234-567812345678",
        "reporting_period_start": "2024-01-01T00:00:00",
        "reporting_period_end": "2024-12-31T23:59:59",
        "activity_data": [
            {
                "category": "purchased_goods_services",
                "activity_type": "Electronics",
                "amount": 100000,
                "unit": "USD"
            }
        ],
        "calculation_method": "activity_based",
        "include_uncertainty": True
    }
    
    print("Sending request to:", url)
    print("Data:", json.dumps(data, indent=2))
    
    response = requests.post(url, json=data)
    
    print(f"\nStatus Code: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=2))
    
    # If it failed, let's check what's in the database
    if response.status_code != 200:
        print("\n--- Checking database state ---")
        
        # Check calculations
        calc_response = requests.get(url)
        calcs = calc_response.json()
        print(f"Existing calculations: {calcs['total']}")
        
        if calcs['calculations']:
            print("\nFirst 3 calculations:")
            for calc in calcs['calculations'][:3]:
                print(f"  - ID: {calc['id']}")
                print(f"    Status: {calc['status']}")
                print(f"    Emissions: {calc['total_emissions']}")

if __name__ == "__main__":
    test_api_error()
