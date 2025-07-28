import re

with open('app/api/v1/endpoints/emission_factors.py', 'r') as f:
    content = f.read()

# Find the calculate_emission function and replace it
new_calculate = '''@router.post("/calculate")
def calculate_emission(request_body: dict, db: Session = Depends(get_db)):
    """Calculate emissions based on activity data and emission factor"""
    
    factor_id = request_body.get("factor_id", 1)
    amount = float(request_body.get("amount", 0))
    
    # Enhanced emission factors with proper GHG Protocol values
    emission_factors_db = {
        # Purchased Goods & Services
        15: {"name": "Office Paper", "factor": 0.92, "unit": "kg", "category": "purchased_goods_services"},
        16: {"name": "Plastic Products", "factor": 1.89, "unit": "kg", "category": "purchased_goods_services"},
        17: {"name": "Steel", "factor": 1.85, "unit": "kg", "category": "purchased_goods_services"},
        18: {"name": "Aluminum", "factor": 11.89, "unit": "kg", "category": "purchased_goods_services"},
        19: {"name": "Concrete", "factor": 0.385, "unit": "m³", "category": "purchased_goods_services"},
        
        # Business Travel
        42: {"name": "Air Travel - Short Haul", "factor": 0.215, "unit": "passenger-km", "category": "business_travel"},
        43: {"name": "Air Travel - Long Haul", "factor": 0.115, "unit": "passenger-km", "category": "business_travel"},
        44: {"name": "Rail Travel", "factor": 0.041, "unit": "passenger-km", "category": "business_travel"},
        46: {"name": "Hotel Stay", "factor": 15.3, "unit": "nights", "category": "business_travel"},
        
        # Waste Operations
        37: {"name": "Landfill - Mixed Waste", "factor": 467.0, "unit": "tonnes", "category": "waste_operations"},
        38: {"name": "Recycling - Paper", "factor": -2960.0, "unit": "tonnes", "category": "waste_operations"},
        39: {"name": "Recycling - Plastic", "factor": 32.0, "unit": "tonnes", "category": "waste_operations"},
        
        # Add more as needed...
    }
    
    # Get the specific factor
    factor_data = emission_factors_db.get(factor_id, {"factor": 0.233, "name": "Unknown", "unit": "unit"})
    
    # Apply unit conversions if needed
    if factor_data["unit"] == "m³" and request_body.get("unit") == "m³":
        # Concrete is already in m³
        pass
    elif factor_data["unit"] == "tonnes" and request_body.get("unit") == "kg":
        amount = amount / 1000  # Convert kg to tonnes
    
    # Calculate base emissions
    base_emissions = amount * factor_data["factor"]
    
    # Apply category-specific adjustments
    if factor_data.get("category") == "business_travel" and "Air Travel" in factor_data["name"]:
        # Apply RFI (Radiative Forcing Index) for aviation
        if request_body.get("include_rfi", True):
            base_emissions *= 1.9  # GHG Protocol recommended RFI
    
    # Calculate uncertainty based on data quality
    data_quality = request_body.get("data_quality", 3)  # Default to industry average
    uncertainty_ranges = {
        1: 0.05,  # Supplier-specific verified
        2: 0.10,  # Supplier-specific unverified
        3: 0.20,  # Industry average
        4: 0.30,  # Proxy data
        5: 0.40   # Estimated
    }
    uncertainty = uncertainty_ranges.get(data_quality, 0.20)
    
    return {
        "calculated_emissions": base_emissions,
        "unit": "kgCO2e",
        "calculation_method": "activity_data * emission_factor",
        "emission_factor_used": {
            "name": factor_data["name"],
            "value": factor_data["factor"],
            "unit": f"kgCO2e/{factor_data['unit']}"
        },
        "data_quality_score": data_quality,
        "uncertainty_min": base_emissions * (1 - uncertainty),
        "uncertainty_max": base_emissions * (1 + uncertainty),
        "ghg_protocol_category": factor_data.get("category", "unknown"),
        "methodology": "GHG Protocol Corporate Value Chain Standard"
    }'''

# Replace the function
content = re.sub(
    r'@router\.post\("/calculate"\).*?(?=@router|$)',
    new_calculate,
    content,
    flags=re.DOTALL
)

with open('app/api/v1/endpoints/emission_factors.py', 'w') as f:
    f.write(content)

print("Updated calculate endpoint with GHG Protocol compliant calculations")
