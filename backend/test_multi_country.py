#!/usr/bin/env python3
"""
Multi-Country Emission Factor Test Script

Verifies the centralized emission factor service architecture by:
1. Logging in to the API
2. Creating emissions for DE, FR, PL electricity
3. Verifying correct factors are applied (0.35, 0.08, 0.70)
4. Asserting calculated amounts are correct
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def check(response, context):
    """Check API response and exit on failure"""
    if response.status_code >= 400:
        print(f"{RED}FAILED{RESET} {context} (HTTP {response.status_code})")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text}")
        sys.exit(1)
    print(f"{GREEN}OK{RESET} {context}")
    return response.json()


def assert_close(actual, expected, tolerance=0.01, message=""):
    """Assert that actual is close to expected within tolerance"""
    if abs(actual - expected) <= tolerance:
        print(f"   {GREEN}PASS{RESET} {message}: {actual:.4f} == {expected:.4f}")
        return True
    else:
        print(f"   {RED}FAIL{RESET} {message}: {actual:.4f} != {expected:.4f}")
        return False


print(f"\n{CYAN}{BOLD}{'='*70}{RESET}")
print(f"{CYAN}{BOLD}   MULTI-COUNTRY EMISSION FACTOR TEST{RESET}")
print(f"{CYAN}{BOLD}   Testing centralized service architecture{RESET}")
print(f"{CYAN}{BOLD}{'='*70}{RESET}\n")

# ============================================================================
# STEP 1: Authentication
# ============================================================================
print(f"{BOLD}--> Step 1: Authentication{RESET}")
login_payload = {"email": "admin@factortrace.com", "password": "password123"}
auth_resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
token_data = check(auth_resp, "Login")
token = token_data["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"   Token: {token[:25]}...\n")

# ============================================================================
# STEP 2: Test Data - Multi-Country Electricity
# ============================================================================
print(f"{BOLD}--> Step 2: Creating Multi-Country Electricity Records{RESET}\n")

test_cases = [
    {
        "name": "Germany (DE)",
        "payload": {
            "scope": 2,
            "category": "Purchased Electricity",
            "activity_type": "Electricity",
            "country_code": "DE",
            "activity_data": 100000.0,  # 100,000 kWh
            "unit": "kWh"
        },
        "expected_factor": 0.35,
        "expected_amount": 100000.0 * 0.35 / 1000  # 35.0 tCO2e
    },
    {
        "name": "France (FR)",
        "payload": {
            "scope": 2,
            "category": "Purchased Electricity",
            "activity_type": "Electricity",
            "country_code": "FR",
            "activity_data": 100000.0,  # 100,000 kWh
            "unit": "kWh"
        },
        "expected_factor": 0.08,
        "expected_amount": 100000.0 * 0.08 / 1000  # 8.0 tCO2e
    },
    {
        "name": "Poland (PL)",
        "payload": {
            "scope": 2,
            "category": "Purchased Electricity",
            "activity_type": "Electricity",
            "country_code": "PL",
            "activity_data": 100000.0,  # 100,000 kWh
            "unit": "kWh"
        },
        "expected_factor": 0.70,
        "expected_amount": 100000.0 * 0.70 / 1000  # 70.0 tCO2e
    },
]

all_passed = True
results = []

for tc in test_cases:
    print(f"   {CYAN}Testing: {tc['name']}{RESET}")
    print(f"   Payload: {tc['payload']['activity_data']} {tc['payload']['unit']} @ {tc['payload']['country_code']}")
    print(f"   Expected Factor: {tc['expected_factor']} kgCO2e/kWh")
    print(f"   Expected Amount: {tc['expected_amount']:.2f} tCO2e")

    # Make API call
    resp = requests.post(f"{BASE_URL}/emissions/", headers=headers, json=tc["payload"])
    data = check(resp, f"Create emission for {tc['name']}")

    # Extract values
    actual_factor = data.get("emission_factor")
    actual_amount = data.get("amount")
    emission_id = data.get("id")

    print(f"   Actual Factor:  {actual_factor}")
    print(f"   Actual Amount:  {actual_amount:.4f} tCO2e")

    # Assertions
    factor_ok = assert_close(actual_factor, tc["expected_factor"], 0.001, "Factor")
    amount_ok = assert_close(actual_amount, tc["expected_amount"], 0.1, "Amount")

    if not factor_ok or not amount_ok:
        all_passed = False

    results.append({
        "country": tc["payload"]["country_code"],
        "emission_id": emission_id,
        "factor": actual_factor,
        "amount": actual_amount,
        "factor_ok": factor_ok,
        "amount_ok": amount_ok
    })

    print()

# ============================================================================
# STEP 3: Summary
# ============================================================================
print(f"{BOLD}--> Step 3: Test Summary{RESET}\n")

print(f"   {'Country':<10} {'Factor':<10} {'Amount (tCO2e)':<15} {'Status'}")
print(f"   {'-'*50}")

for r in results:
    status = f"{GREEN}PASS{RESET}" if r["factor_ok"] and r["amount_ok"] else f"{RED}FAIL{RESET}"
    print(f"   {r['country']:<10} {r['factor']:<10.2f} {r['amount']:<15.2f} {status}")

print()

# ============================================================================
# STEP 4: Test Missing Factor (422 Error)
# ============================================================================
print(f"{BOLD}--> Step 4: Testing 422 Error for Missing Factor{RESET}")

missing_payload = {
    "scope": 2,
    "category": "Unknown Category",
    "activity_type": "Unknown Activity",
    "country_code": "XX",
    "activity_data": 1000.0,
    "unit": "units"
}

resp = requests.post(f"{BASE_URL}/emissions/", headers=headers, json=missing_payload)

if resp.status_code == 422:
    error_detail = resp.json().get("detail", "")
    print(f"   {GREEN}PASS{RESET} Received 422 error as expected")
    print(f"   Error message: {error_detail}")
    if "No emission factor found for key" in error_detail:
        print(f"   {GREEN}PASS{RESET} Error message contains the missing key")
    else:
        print(f"   {YELLOW}WARN{RESET} Error message format unexpected")
else:
    print(f"   {RED}FAIL{RESET} Expected 422, got {resp.status_code}")
    all_passed = False

print()

# ============================================================================
# STEP 5: Test Manual Override
# ============================================================================
print(f"{BOLD}--> Step 5: Testing Manual Override{RESET}")

override_payload = {
    "scope": 2,
    "category": "Purchased Electricity",
    "activity_type": "Electricity",
    "country_code": "DE",
    "activity_data": 1000.0,
    "unit": "kWh",
    "emission_factor": 0.99  # Manual override
}

resp = requests.post(f"{BASE_URL}/emissions/", headers=headers, json=override_payload)
data = check(resp, "Create emission with manual override")

if data.get("emission_factor") == 0.99:
    print(f"   {GREEN}PASS{RESET} Manual override factor 0.99 was used")
    expected_amount = 1000.0 * 0.99 / 1000  # 0.99 tCO2e
    if abs(data.get("amount") - expected_amount) < 0.01:
        print(f"   {GREEN}PASS{RESET} Amount calculated correctly: {data.get('amount'):.4f} tCO2e")
    else:
        print(f"   {RED}FAIL{RESET} Amount incorrect: {data.get('amount')}")
        all_passed = False
else:
    print(f"   {RED}FAIL{RESET} Manual override was not applied")
    all_passed = False

print()

# ============================================================================
# Final Result
# ============================================================================
print(f"{BOLD}{'='*70}{RESET}")
if all_passed:
    print(f"{GREEN}{BOLD}   ALL TESTS PASSED - Architecture is solid!{RESET}")
else:
    print(f"{RED}{BOLD}   SOME TESTS FAILED - Review the output above{RESET}")
print(f"{BOLD}{'='*70}{RESET}\n")

sys.exit(0 if all_passed else 1)
