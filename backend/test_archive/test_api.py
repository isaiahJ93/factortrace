import requests
import json

BASE_URL = "http://localhost:8000/api/v1/emissions"

print("🧪 Testing FactorTrace API Endpoints\n")

# Test 1: Simple calculation
print("1️⃣ Simple Calculation:")
response = requests.post(f"{BASE_URL}/calculate/simple", json={
    "activity_value": 1000,
    "emission_factor": 0.233,
    "unit": "kgCO2e",
    "uncertainty_percent": 10.0
})
print(f"   Result: {response.json()['emissions']:.3f} {response.json()['unit']}\n")

# Test 2: Advanced calculation with Diesel
print("2️⃣ Advanced Calculation (Diesel):")
response = requests.post(f"{BASE_URL}/calculate/advanced", json={
    "activity_data": [{
        "activity_amount": 100,
        "activity_unit": "liter",
        "emission_factor_id": "Diesel"
    }],
    "calculation_options": {
        "uncertainty_method": "monte_carlo",
        "confidence_level": 95
    }
})
result = response.json()
print(f"   Emissions: {result['emissions_tco2e']:.3f} tCO2e")
print(f"   Uncertainty: ±{result['uncertainty_percent']:.1f}%")
print(f"   95% CI: [{result['confidence_interval']['lower']:.3f}, {result['confidence_interval']['upper']:.3f}]\n")

# Test 3: Scope 3 calculation
print("3️⃣ Scope 3 - Purchased Goods:")
response = requests.post(f"{BASE_URL}/calculate/scope3/purchased_goods_services", json={
    "Steel (Virgin)": {"amount": 1000, "unit": "kg"},
    "Aluminum (Primary)": {"amount": 500, "unit": "kg"}
})
if response.status_code == 200:
    result = response.json()
    print(f"   Total: {result['emissions_tco2e']:.3f} tCO2e")
else:
    print(f"   Error: {response.json()['detail']}")

# Test 4: Materiality assessment
print("\n4️⃣ Materiality Assessment:")
response = requests.post(f"{BASE_URL}/materiality/assess", json={
    "sector": "Manufacturing",
    "current_emissions": {
        "purchased_goods_services": 45000,
        "business_travel": 5000
    }
})
assessments = response.json()['assessments']
material_count = sum(1 for a in assessments if a['is_material'])
print(f"   Material categories: {material_count}/{len(assessments)}")

# Test 5: Get all Scope 3 categories
print("\n5️⃣ Available Scope 3 Categories:")
response = requests.get(f"{BASE_URL}/scope3/categories")
categories = response.json()
for i, (key, info) in enumerate(list(categories.items())[:5]):
    print(f"   {info['id']}: {info['display_name']}")
print("   ... and 10 more categories")

print("\n✅ All tests completed!")
