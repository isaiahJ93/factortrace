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
# We verify Official EFRAG Taxonomy tags (verified from esrs_taxonomy.xlsx):
#   - esrs:GrossScope1GreenhouseGasEmissions
#   - esrs:GrossLocationBasedScope2GreenhouseGasEmissions
#   - esrs:GrossScope3GreenhouseGasEmissions

print("\n--> Step 4: Verifying EFRAG Taxonomy Tags...")

# Check for Official EFRAG tag names (full "GreenhouseGasEmissions" not "GHGEmissions")
tag_scope1 = "GrossScope1GreenhouseGasEmissions" in content
tag_scope2 = "GrossLocationBasedScope2GreenhouseGasEmissions" in content
tag_scope3 = "GrossScope3GreenhouseGasEmissions" in content

print(f"   esrs:GrossScope1GreenhouseGasEmissions: {'✅' if tag_scope1 else '❌'}")
print(f"   esrs:GrossLocationBasedScope2GreenhouseGasEmissions: {'✅' if tag_scope2 else '❌'}")
print(f"   esrs:GrossScope3GreenhouseGasEmissions: {'✅' if tag_scope3 else '❌'}")

# Note: The XML might format numbers as "2.65" or "2.6500" or "2,65" depending on locale.
# We search loosely.

# Check Scope 1 (Diesel ~ 2.65)
s1_found = "2.65" in content or "2,65" in content
# Check Scope 2 (Elec ~ 3.5)
s2_found = "3.5" in content or "3,5" in content

print(f"\n--> Step 5: Verifying Database Values in Report...")
print(f"   Scope 1 value (2.65): {'✅' if s1_found else '❌'}")
print(f"   Scope 2 value (3.5): {'✅' if s2_found else '❌'}")

# Final verdict
all_tags_ok = tag_scope1 and tag_scope2 and tag_scope3
all_values_ok = s1_found and s2_found

if all_tags_ok and all_values_ok:
    print(f"\n{GREEN}✨ SUCCESS: EFRAG taxonomy tags AND database values verified! ✨{RESET}")
    print("   The pipeline is FULLY WIRED with Official EFRAG tags.")
elif all_values_ok:
    print(f"\n{GREEN}⚠️  PARTIAL SUCCESS: Database values found but check tag names.{RESET}")
elif all_tags_ok:
    print(f"\n{GREEN}⚠️  PARTIAL SUCCESS: Tags correct but values not found.{RESET}")
else:
    print(f"\n{RED}❌ FAILURE: Report has issues.{RESET}")
    print("   Check tag names and database wiring.")
    print("   Snippet of report:")
    print(content[:500])

