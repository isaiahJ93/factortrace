#!/usr/bin/env python3
"""
Seed Test Data Script
Creates 5 distinct emission records to test aggregation logic.
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def check(response, context):
    if response.status_code >= 400:
        print(f"{RED}FAILED {context} ({response.status_code}){RESET}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
        sys.exit(1)
    print(f"{GREEN}OK{RESET} {context}")
    return response.json()

print(f"{CYAN}{'='*60}{RESET}")
print(f"{CYAN}   SEED TEST DATA - Aggregation Verification{RESET}")
print(f"{CYAN}{'='*60}{RESET}\n")

# 1. AUTHENTICATION
print("--> Step 1: Logging in...")
login_payload = {"email": "admin@factortrace.com", "password": "password123"}
auth_resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
token_data = check(auth_resp, "Authentication")
token = token_data["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"   Token: {token[:20]}...\n")

# 2. CREATE TEST RECORDS
print("--> Step 2: Creating 5 Emission Records...")
print()

test_records = [
    {
        "name": "Scope 2 - Electricity DE",
        "payload": {
            "scope": 2,
            "category": "Purchased Electricity",
            "country": "DE",
            "activity_data": 120000.0,
            "unit": "kWh",
            "description": "German electricity consumption"
        },
        "expected_factor": 0.35,
        "expected_amount": 120000 * 0.35 / 1000  # 42.0 tCO2e
    },
    {
        "name": "Scope 2 - Electricity FR",
        "payload": {
            "scope": 2,
            "category": "Purchased Electricity",
            "country": "FR",
            "activity_data": 80000.0,
            "unit": "kWh",
            "description": "French electricity consumption"
        },
        "expected_factor": 0.08,
        "expected_amount": 80000 * 0.08 / 1000  # 6.4 tCO2e
    },
    {
        "name": "Scope 2 - Electricity PL",
        "payload": {
            "scope": 2,
            "category": "Purchased Electricity",
            "country": "PL",
            "activity_data": 50000.0,
            "unit": "kWh",
            "description": "Polish electricity consumption"
        },
        "expected_factor": 0.70,
        "expected_amount": 50000 * 0.70 / 1000  # 35.0 tCO2e
    },
    {
        "name": "Scope 3 - Water Supply DE",
        "payload": {
            "scope": 3,
            "category": "Water Supply",
            "country": "DE",
            "activity_data": 3000.0,
            "unit": "m3",
            "description": "Water consumption"
        },
        "expected_factor": 0.30,
        "expected_amount": 3000 * 0.30 / 1000  # 0.9 tCO2e
    },
    {
        "name": "Scope 3 - Business Travel DE",
        "payload": {
            "scope": 3,
            "category": "Business Travel",
            "country": "DE",
            "activity_data": 6600.0,
            "unit": "km",
            "description": "Business travel emissions"
        },
        "expected_factor": 0.15,
        "expected_amount": 6600 * 0.15 / 1000  # 0.99 tCO2e
    },
]

created_ids = []
total_expected = {
    "scope1": 0.0,
    "scope2": 0.0,
    "scope3": 0.0,
}

for record in test_records:
    print(f"   Creating: {record['name']}")
    print(f"      Activity: {record['payload']['activity_data']} {record['payload']['unit']}")
    print(f"      Expected Factor: {record['expected_factor']} kgCO2e/{record['payload']['unit']}")
    print(f"      Expected Amount: {record['expected_amount']:.2f} tCO2e")

    resp = requests.post(f"{BASE_URL}/emissions/", headers=headers, json=record['payload'])
    data = check(resp, f"Create {record['name']}")

    created_ids.append(data.get("id"))
    actual_amount = data.get("amount", 0)

    # Track totals by scope
    scope_key = f"scope{record['payload']['scope']}"
    total_expected[scope_key] += record['expected_amount']

    # Check if amount matches expected
    if abs(actual_amount - record['expected_amount']) < 0.1:
        print(f"      {GREEN}Actual Amount: {actual_amount:.2f} tCO2e (matches!){RESET}")
    else:
        print(f"      {YELLOW}Actual Amount: {actual_amount:.2f} tCO2e (expected {record['expected_amount']:.2f}){RESET}")
    print()

print(f"{CYAN}Created emission IDs: {created_ids}{RESET}\n")

# 3. EXPECTED TOTALS
print("--> Step 3: Expected Totals:")
print(f"   Scope 1: {total_expected['scope1']:.2f} tCO2e")
print(f"   Scope 2: {total_expected['scope2']:.2f} tCO2e (42.0 + 6.4 + 35.0 = 83.4)")
print(f"   Scope 3: {total_expected['scope3']:.2f} tCO2e (0.9 + 0.99 = 1.89)")
print(f"   Total:   {sum(total_expected.values()):.2f} tCO2e")
print()

# 4. FETCH SUMMARY
print("--> Step 4: Fetching Emissions Summary...")
summary_resp = requests.get(f"{BASE_URL}/emissions/summary", headers=headers)
summary = check(summary_resp, "Get Summary")

print(f"\n{CYAN}{'='*60}{RESET}")
print(f"{CYAN}   SUMMARY RESPONSE{RESET}")
print(f"{CYAN}{'='*60}{RESET}")
print(json.dumps(summary, indent=2, default=str))

# 5. VALIDATE SUMMARY
print(f"\n{CYAN}{'='*60}{RESET}")
print(f"{CYAN}   VALIDATION{RESET}")
print(f"{CYAN}{'='*60}{RESET}")

# Check scope totals (handles both key naming conventions)
scope1_actual = summary.get("scope1_total", summary.get("scope1_emissions", 0))
scope2_actual = summary.get("scope2_total", summary.get("scope2_emissions", 0))
scope3_actual = summary.get("scope3_total", summary.get("scope3_emissions", 0))

print(f"\nScope 1 Total: {scope1_actual:.2f} tCO2e")
print(f"Scope 2 Total: {scope2_actual:.2f} tCO2e")
print(f"Scope 3 Total: {scope3_actual:.2f} tCO2e")
print(f"Grand Total:   {scope1_actual + scope2_actual + scope3_actual:.2f} tCO2e")

# Check if totals include at least our new records
print(f"\n{CYAN}Checking aggregation includes new records:{RESET}")

# Scope 2 should include at least 83.4 tCO2e from new records
if scope2_actual >= 83.0:
    print(f"   Scope 2: {GREEN}PASS{RESET} (includes >= 83.4 from new records)")
else:
    print(f"   Scope 2: {RED}FAIL{RESET} (expected at least 83.4 tCO2e)")

# Scope 3 should include at least 1.89 tCO2e from new records
if scope3_actual >= 1.8:
    print(f"   Scope 3: {GREEN}PASS{RESET} (includes >= 1.89 from new records)")
else:
    print(f"   Scope 3: {RED}FAIL{RESET} (expected at least 1.89 tCO2e)")

# Check category breakdown
by_category = summary.get("by_category", {})
if by_category:
    print(f"\nCategory Breakdown:")
    for cat, val in by_category.items():
        print(f"   {cat}: {val:.2f} tCO2e")

print(f"\n{GREEN}{'='*60}{RESET}")
print(f"{GREEN}   SEED DATA COMPLETE{RESET}")
print(f"{GREEN}{'='*60}{RESET}")
