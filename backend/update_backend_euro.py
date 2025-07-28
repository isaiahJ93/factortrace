# Add to EMISSION_FACTORS in ghg_monte_carlo_api.py

EUR_FACTORS = {
    # Economic Input-Output factors (EUR-based)
    "electronics": {"factor": 0.39, "unit": "EUR", "scope": "scope_3", "ef_uncertainty": 25.0},
    "food_beverages": {"factor": 0.35, "unit": "EUR", "scope": "scope_3", "ef_uncertainty": 25.0},
    "machinery": {"factor": 0.32, "unit": "EUR", "scope": "scope_3", "ef_uncertainty": 20.0},
    "buildings": {"factor": 0.26, "unit": "EUR", "scope": "scope_3", "ef_uncertainty": 20.0},
    "vehicles": {"factor": 0.37, "unit": "EUR", "scope": "scope_3", "ef_uncertainty": 20.0},
    "franchise_travel": {"factor": 0.14, "unit": "EUR", "scope": "scope_3", "ef_uncertainty": 30.0},
    
    # Investment factors (EUR millions)
    "equity_investments": {"factor": 630.0, "unit": "EUR million", "scope": "scope_3", "ef_uncertainty": 30.0},
    "debt_investments": {"factor": 325.0, "unit": "EUR million", "scope": "scope_3", "ef_uncertainty": 30.0},
    "project_finance": {"factor": 415.0, "unit": "EUR million", "scope": "scope_3", "ef_uncertainty": 30.0},
    "investment_funds": {"factor": 510.0, "unit": "EUR million", "scope": "scope_3", "ef_uncertainty": 30.0}
}

print("Add these EUR factors to your EMISSION_FACTORS dictionary in ghg_monte_carlo_api.py")
for key, value in EUR_FACTORS.items():
    print(f'    "{key}": {value},')
