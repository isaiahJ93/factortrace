#!/usr/bin/env python3
"""Test script to verify scope lookup and cascading dropdown endpoints."""

import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"


def test_categories_endpoint():
    """Test the /emissions/categories endpoint."""
    print("\n" + "=" * 60)
    print("Testing /emissions/categories endpoint")
    print("=" * 60)

    # Test scope 1
    response = requests.get(f"{BASE_URL}/emissions/categories", params={"scope": 1})
    print(f"\nScope 1: {response.status_code}")
    data = response.json()
    print(f"  Categories: {data}")
    assert isinstance(data, list), "Expected list response"
    assert "stationary_combustion" in data, "Expected 'stationary_combustion' in scope 1"

    # Test scope 2
    response = requests.get(f"{BASE_URL}/emissions/categories", params={"scope": 2})
    print(f"\nScope 2: {response.status_code}")
    data = response.json()
    print(f"  Categories: {data}")
    assert isinstance(data, list), "Expected list response"
    assert "electricity" in data, "Expected 'electricity' in scope 2"

    # Test scope 3
    response = requests.get(f"{BASE_URL}/emissions/categories", params={"scope": 3})
    print(f"\nScope 3: {response.status_code}")
    data = response.json()
    print(f"  Categories: {data}")
    assert isinstance(data, list), "Expected list response"
    assert "business_travel" in data, "Expected 'business_travel' in scope 3"
    assert len(data) >= 10, f"Expected at least 10 scope 3 categories, got {len(data)}"

    print("\n✅ Categories endpoint tests PASSED")


def test_factors_endpoint():
    """Test the /emissions/factors endpoint."""
    print("\n" + "=" * 60)
    print("Testing /emissions/factors endpoint")
    print("=" * 60)

    # Test business_travel category
    response = requests.get(f"{BASE_URL}/emissions/factors", params={"category": "business_travel"})
    print(f"\nCategory 'business_travel': {response.status_code}")
    data = response.json()
    print(f"  Activity types: {[f['activity_type'] for f in data]}")
    assert isinstance(data, list), "Expected list response"
    assert len(data) > 0, "Expected at least one activity type"
    assert all("activity_type" in f for f in data), "Each factor should have 'activity_type'"
    assert all("unit" in f for f in data), "Each factor should have 'unit'"
    assert all("factor_value" in f for f in data), "Each factor should have 'factor_value'"

    # Test electricity category
    response = requests.get(f"{BASE_URL}/emissions/factors", params={"category": "electricity"})
    print(f"\nCategory 'electricity': {response.status_code}")
    data = response.json()
    print(f"  Activity types: {[f['activity_type'] for f in data]}")
    assert isinstance(data, list), "Expected list response"
    assert len(data) > 0, "Expected at least one activity type for electricity"

    # Test non-existent category
    response = requests.get(f"{BASE_URL}/emissions/factors", params={"category": "nonexistent"})
    print(f"\nCategory 'nonexistent': {response.status_code}")
    data = response.json()
    print(f"  Result: {data}")
    assert isinstance(data, list), "Expected list response"
    assert len(data) == 0, "Expected empty list for nonexistent category"

    print("\n✅ Factors endpoint tests PASSED")


def test_emission_factors_categories():
    """Test the /emission-factors/categories endpoint."""
    print("\n" + "=" * 60)
    print("Testing /emission-factors/categories endpoint")
    print("=" * 60)

    # Test scope 3
    response = requests.get(f"{BASE_URL}/emission-factors/categories", params={"scope": 3})
    print(f"\nScope 3: {response.status_code}")
    data = response.json()
    print(f"  Categories: {data}")
    assert isinstance(data, list), "Expected list response"
    assert len(data) > 0, "Expected categories for scope 3"

    print("\n✅ Emission factors categories endpoint tests PASSED")


def test_full_cascade():
    """Test the full cascading dropdown flow."""
    print("\n" + "=" * 60)
    print("Testing Full Cascade Flow (Scope -> Category -> Activity Type)")
    print("=" * 60)

    # Step 1: Get categories for scope 3
    print("\n1. Select Scope 3...")
    response = requests.get(f"{BASE_URL}/emissions/categories", params={"scope": 3})
    categories = response.json()
    print(f"   Available categories: {categories[:5]}..." if len(categories) > 5 else f"   Categories: {categories}")

    # Step 2: Select a category
    selected_category = "business_travel"
    print(f"\n2. Select category: {selected_category}")
    response = requests.get(f"{BASE_URL}/emissions/factors", params={"category": selected_category})
    activity_types = response.json()
    print(f"   Available activity types: {[a['activity_type'] for a in activity_types]}")

    # Step 3: Select an activity type
    if activity_types:
        selected = activity_types[0]
        print(f"\n3. Select activity type: {selected['activity_type']}")
        print(f"   Auto-filled unit: {selected['unit']}")
        print(f"   Emission factor: {selected['factor_value']} kgCO2e/{selected['unit']}")

    print("\n✅ Full cascade flow test PASSED")


if __name__ == "__main__":
    try:
        test_categories_endpoint()
        test_factors_endpoint()
        test_emission_factors_categories()
        test_full_cascade()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        sys.exit(0)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend at", BASE_URL)
        print("   Make sure the backend is running: uvicorn app.main:app --reload")
        sys.exit(1)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
