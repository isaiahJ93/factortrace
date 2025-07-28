# In app/api/v1/endpoints/ghg_calculator.py, update the mapping:

FRONTEND_TO_BACKEND_MAPPING = {
    # Keep the original IDs, just map the factors
    "electricity_grid": "electricity",
    "natural_gas_stationary": "natural gas",
    "diesel_fleet": "diesel",
    "petrol_fleet": "gasoline",
    # Add more as needed
}

# But in the response, use the ORIGINAL activity_type:
# Around line 250 in calculate_with_monte_carlo:
for idx, item in enumerate(request.get("emissions_data", [])):
    original_type = item["activity_type"]  # Keep the original!
    backend_type = FRONTEND_TO_BACKEND_MAPPING.get(original_type, original_type)
    
    # Use backend_type for calculation, but return original_type
    emissions_data.append({
        "activity_type": backend_type,  # For calculation
        "original_type": original_type,  # To return to frontend
        "amount": item["amount"],
        "unit": item["unit"]
    })

# Then in the response, use original_type:
"activity_type": item["original_type"],  # Return what frontend sent
