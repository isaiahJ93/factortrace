#!/usr/bin/env python3
"""
Test CSV Loading for Emission Factors

Verifies that the CSV-backed emission factor service loads correctly
and preserves the expected values.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.emission_factors import FACTOR_DB, get_factor


def test_factor_db_de_electricity():
    """Test that DE electricity factor is loaded correctly"""
    key = ("SCOPE_2", "Purchased Electricity", "Electricity", "DE")
    assert key in FACTOR_DB, f"Key {key} not found in FACTOR_DB"
    assert FACTOR_DB[key] == 0.35, f"Expected 0.35, got {FACTOR_DB[key]}"
    print(f"PASS: {key} = {FACTOR_DB[key]}")


def test_factor_db_pl_electricity():
    """Test that PL electricity factor is loaded correctly"""
    key = ("SCOPE_2", "Purchased Electricity", "Electricity", "PL")
    assert key in FACTOR_DB, f"Key {key} not found in FACTOR_DB"
    assert FACTOR_DB[key] == 0.70, f"Expected 0.70, got {FACTOR_DB[key]}"
    print(f"PASS: {key} = {FACTOR_DB[key]}")


def test_factor_db_fr_electricity():
    """Test that FR electricity factor is loaded correctly"""
    key = ("SCOPE_2", "Purchased Electricity", "Electricity", "FR")
    assert key in FACTOR_DB, f"Key {key} not found in FACTOR_DB"
    assert FACTOR_DB[key] == 0.08, f"Expected 0.08, got {FACTOR_DB[key]}"
    print(f"PASS: {key} = {FACTOR_DB[key]}")


def test_factor_db_water_supply():
    """Test that Water Supply factor is loaded correctly"""
    key = ("SCOPE_3", "Water Supply", "Water", "DE")
    assert key in FACTOR_DB, f"Key {key} not found in FACTOR_DB"
    assert FACTOR_DB[key] == 0.30, f"Expected 0.30, got {FACTOR_DB[key]}"
    print(f"PASS: {key} = {FACTOR_DB[key]}")


def test_factor_db_business_travel_de():
    """Test that Business Travel DE factor is loaded correctly"""
    key = ("SCOPE_3", "Business Travel", "Flight", "DE")
    assert key in FACTOR_DB, f"Key {key} not found in FACTOR_DB"
    assert FACTOR_DB[key] == 0.15, f"Expected 0.15, got {FACTOR_DB[key]}"
    print(f"PASS: {key} = {FACTOR_DB[key]}")


def test_factor_db_business_travel_us():
    """Test that Business Travel US factor is loaded correctly"""
    key = ("SCOPE_3", "Business Travel", "Flight", "US")
    assert key in FACTOR_DB, f"Key {key} not found in FACTOR_DB"
    assert FACTOR_DB[key] == 0.12, f"Expected 0.12, got {FACTOR_DB[key]}"
    print(f"PASS: {key} = {FACTOR_DB[key]}")


def test_get_factor_function():
    """Test get_factor function with various inputs"""
    # Test with integer scope
    factor = get_factor(2, "Purchased Electricity", "Electricity", "DE")
    assert factor == 0.35, f"Expected 0.35, got {factor}"
    print(f"PASS: get_factor(2, 'Purchased Electricity', 'Electricity', 'DE') = {factor}")

    # Test with string scope
    factor = get_factor("SCOPE_2", "Purchased Electricity", "Electricity", "PL")
    assert factor == 0.70, f"Expected 0.70, got {factor}"
    print(f"PASS: get_factor('SCOPE_2', 'Purchased Electricity', 'Electricity', 'PL') = {factor}")


def test_hardcoded_fallback():
    """Test that hardcoded values still work (UK not in CSV)"""
    key = ("SCOPE_2", "Purchased Electricity", "Electricity", "UK")
    assert key in FACTOR_DB, f"Key {key} not found - hardcoded fallback failed"
    assert FACTOR_DB[key] == 0.23, f"Expected 0.23 (hardcoded), got {FACTOR_DB[key]}"
    print(f"PASS: Hardcoded fallback {key} = {FACTOR_DB[key]}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("  CSV LOADING TESTS")
    print("=" * 60)
    print()

    tests = [
        test_factor_db_de_electricity,
        test_factor_db_pl_electricity,
        test_factor_db_fr_electricity,
        test_factor_db_water_supply,
        test_factor_db_business_travel_de,
        test_factor_db_business_travel_us,
        test_get_factor_function,
        test_hardcoded_fallback,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__}: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
