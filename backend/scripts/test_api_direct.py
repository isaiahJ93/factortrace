#!/usr/bin/env python3
"""Test the API directly to see errors"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_ghg_calculation():
    # Test data
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
    
    print("Sending request...")
    print(json.dumps(data, indent=2))
    
    try:
        response = client.post("/api/v1/ghg/calculations/", json=data)
        print(f"\nStatus code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code != 200:
            # Try to get more error details
            print("\nChecking server state...")
            
            # Check organizations
            org_response = client.get("/api/v1/ghg/calculations/")
            print(f"Existing calculations: {org_response.json()}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ghg_calculation()
