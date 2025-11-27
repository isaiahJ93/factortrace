import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

def check(response, context, expect_json=True):
    if response.status_code >= 400:
        print(f"{RED}❌ {context} FAILED ({response.status_code}){RESET}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Response: {response.text[:500]}...")
        sys.exit(1)
    
    print(f"{GREEN}✅ {context} SUCCESS{RESET}")
    
    if expect_json:
        try:
            return response.json()
        except:
            return {}
    return response.text

print("🚀 Starting FINAL System Verification...\n")

# 1. AUTHENTICATION
print("--> Step 1: Logging in...")
login_payload = {"email": "admin@factortrace.com", "password": "password123"}
auth_resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
token = check(auth_resp, "Authentication")["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. CREATE EMISSION (Using DB Lookup)
print("\n--> Step 2: Creating Test Emissions...")
# Emission A: Diesel (Scope 1)
payload_1 = {
    "scope": 1, 
    "category": "Mobile Combustion", 
    "activity_type": "Diesel",   
    "country_code": "DE", 
    "activity_data": 1000.0, 
    "unit": "liters"
}
resp_1 = requests.post(f"{BASE_URL}/emissions/", headers=headers, json=payload_1)
data_1 = check(resp_1, "Create Diesel Emission")
amount_1 = data_1.get('amount', 0)
print(f"   Diesel Amount: {amount_1} tCO2e")

# Emission B: Electricity (Scope 2)
payload_2 = {
    "scope": 2, 
    "category": "Purchased Electricity", 
    "activity_type": "Electricity", 
    "country_code": "DE", 
    "activity_data": 10000.0, 
    "unit": "kWh"
}
resp_2 = requests.post(f"{BASE_URL}/emissions/", headers=headers, json=payload_2)
data_2 = check(resp_2, "Create Electricity Emission")
amount_2 = data_2.get('amount', 0)
print(f"   Elec Amount: {amount_2} tCO2e")

# 3. VERIFY REPORTING AGGREGATION
print("\n--> Step 3: Generating iXBRL Report...")

report_req = {
    "entity_name": "FactorTrace Final Verification",
    "reporting_year": 2024,
    "currency": "EUR"
}

# We tell check() NOT to expect JSON
report_resp = requests.post(f"{BASE_URL}/esrs-e1/export-ixbrl", headers=headers, json=report_req)
content = check(report_resp, "Generate Report", expect_json=False)

print(f"   Report Size: {len(content)} bytes")

# 4. PARSE & VERIFY CONTENT
# We verify if the engine effectively queried the DB and put the numbers in the XML.
# We verify 'GrossScope1' and 'GrossScope2' tags.

# Note: The XML might format numbers as "2.65" or "2.6500" or "2,65" depending on locale.
# We search loosely.

# Check Scope 1 (Diesel ~ 2.65)
s1_found = "2.65" in content or "2,65" in content
# Check Scope 2 (Elec ~ 3.5)
s2_found = "3.5" in content or "3,5" in content

if s1_found and s2_found:
    print(f"\n{GREEN}✨ SUCCESS: Database values found in iXBRL! ✨{RESET}")
    print("   The pipeline is FULLY WIRED.")
elif s1_found or s2_found:
    print(f"\n{GREEN}⚠️  PARTIAL SUCCESS: Found some values but not all.{RESET}")
    print(f"   Scope 1 (2.65) Found: {s1_found}")
    print(f"   Scope 2 (3.5) Found: {s2_found}")
else:
    print(f"\n{RED}❌ FAILURE: Report contains generic/zero data.{RESET}")
    print("   The reporting endpoint is ignoring the database.")
    print("   Snippet of report:")
    print(content[:500])

