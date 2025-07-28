"""
Add this to app/api/v1/endpoints/ghg_calculator.py
Or run this script to append it automatically
"""

MONTE_CARLO_ENDPOINT = '''
# Frontend activity type mapping
FRONTEND_TO_BACKEND_MAPPING = {
    # Scope 1
    "natural_gas_stationary": "natural gas",
    "diesel_stationary": "diesel",
    "lpg_stationary": "lpg", 
    "coal": "coal",
    "fuel_oil": "fuel oil",
    "diesel_fleet": "diesel",
    "petrol_fleet": "gasoline",
    "refrigerant_hfc": "refrigerants",
    "refrigerant_r410a": "refrigerants",
    
    # Scope 2
    "electricity_grid": "electricity",
    "electricity_renewable": "renewable electricity",
    "district_heating": "district heating",
    "purchased_steam": "purchased steam",
    "district_cooling": "district cooling",
    
    # Scope 3
    "air_travel_short": "business travel - air",
    "air_travel_medium": "business travel - air", 
    "air_travel_long": "business travel - air",
    "rail_travel": "business travel - rail",
    "employee_commuting_car": "employee commuting",
    "upstream_transport_road": "upstream transportation - road",
    "downstream_transport_road": "downstream transportation - road",
    "waste_landfill": "waste disposal",
    "business_services": "purchased goods and services",
    "cloud_computing": "purchased goods and services",
    "wfh_electricity": "remote work"
}

@router.post("/calculate-with-monte-carlo")
async def calculate_with_monte_carlo(
    request: dict,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Calculate emissions with Monte Carlo uncertainty analysis"""
    import numpy as np
    
    # Extract parameters
    reporting_period = request.get("reporting_period", str(datetime.now().year))
    emissions_data = request.get("emissions_data", [])
    monte_carlo_iterations = request.get("monte_carlo_iterations", 1000)
    include_uncertainty = request.get("include_uncertainty", True)
    
    # Map frontend activity types to backend
    mapped_emissions_data = []
    for item in emissions_data:
        frontend_type = item["activity_type"]
        backend_type = FRONTEND_TO_BACKEND_MAPPING.get(frontend_type, frontend_type)
        
        mapped_emissions_data.append({
            "activity_type": backend_type,
            "amount": item["amount"],
            "unit": item["unit"]
        })
    
    # Calculate base emissions using existing function
    calc_request = CalculateEmissionsRequest(
        reporting_period=reporting_period,
        emissions_data=mapped_emissions_data
    )
    
    base_result = calculate_emissions(calc_request)
    
    # Monte Carlo simulation if requested
    uncertainty_analysis = None
    if include_uncertainty and monte_carlo_iterations > 0:
        results = []
        
        for _ in range(monte_carlo_iterations):
            varied_total = 0
            varied_scope1 = 0
            varied_scope2 = 0
            varied_scope3 = 0
            
            for idx, activity in enumerate(mapped_emissions_data):
                # Get uncertainty percentage from original data
                uncertainty = emissions_data[idx].get("uncertainty_percentage", 10) / 100
                
                # Apply uncertainty to emission factor
                factor_variation = np.random.normal(1.0, uncertainty)
                
                activity_type = activity["activity_type"]
                if activity_type in EMISSION_FACTORS:
                    factor_info = EMISSION_FACTORS[activity_type]
                    base_factor = factor_info["factor"]
                    scope = factor_info["scope"]
                    
                    varied_factor = base_factor * factor_variation
                    emission = activity["amount"] * varied_factor / 1000  # tons
                    
                    varied_total += emission
                    if scope == 1:
                        varied_scope1 += emission
                    elif scope == 2:
                        varied_scope2 += emission
                    else:
                        varied_scope3 += emission
            
            results.append({
                "total": varied_total,
                "scope1": varied_scope1,
                "scope2": varied_scope2,
                "scope3": varied_scope3
            })
        
        # Calculate statistics
        totals = [r["total"] for r in results]
        
        uncertainty_analysis = {
            "monte_carlo_runs": monte_carlo_iterations,
            "mean_emissions": float(np.mean(totals)),
            "std_deviation": float(np.std(totals)),
            "confidence_interval_95": {
                "lower": float(np.percentile(totals, 2.5)),
                "upper": float(np.percentile(totals, 97.5))
            },
            "relative_uncertainty_percent": float((np.std(totals) / np.mean(totals)) * 100) if np.mean(totals) > 0 else 0
        }
    
    # Return in frontend's expected format
    return {
        "summary": {
            "total_emissions_tons_co2e": base_result["total_emissions"],
            "scope1_emissions": base_result["by_scope"]["scope_1"] * 1000,  # kg
            "scope2_location_based": base_result["by_scope"]["scope_2"] * 1000,
            "scope2_market_based": base_result["by_scope"]["scope_2"] * 1000,
            "scope3_emissions": base_result["by_scope"]["scope_3"] * 1000,
        },
        "by_activity": base_result["by_activity"],
        "uncertainty_analysis": uncertainty_analysis,
        "reporting_period": reporting_period,
        "calculation_date": datetime.now().isoformat()
    }
'''

if __name__ == "__main__":
    import os
    
    # Path to the ghg_calculator.py file
    calculator_path = "app/api/v1/endpoints/ghg_calculator.py"
    
    if os.path.exists(calculator_path):
        # Read the current file
        with open(calculator_path, 'r') as f:
            content = f.read()
        
        # Check if endpoint already exists
        if "calculate-with-monte-carlo" not in content:
            # Add imports if needed
            if "import numpy as np" not in content:
                content = "import numpy as np\n" + content
            
            # Append the new endpoint
            with open(calculator_path, 'a') as f:
                f.write("\n\n" + MONTE_CARLO_ENDPOINT)
            
            print("✅ Monte Carlo endpoint added successfully!")
            print("🚀 The frontend calculator should now work perfectly!")
        else:
            print("⚠️ Monte Carlo endpoint already exists")
    else:
        print(f"❌ Could not find {calculator_path}")
        print("📝 Copy the endpoint code from above and add it manually")
