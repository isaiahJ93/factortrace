# Add this to ghg_monte_carlo_api.py to replace the EMISSION_FACTORS dictionary

EMISSION_FACTORS = {
    # Waste
    "waste_landfill": {"factor": 467.0, "unit": "tonnes", "scope": "scope_3", "ef_uncertainty": 20.0},
    "waste_scrap_metal": {"factor": 21.0, "unit": "tonnes", "scope": "scope_3", "ef_uncertainty": 15.0},
    "waste_recycled": {"factor": 21.0, "unit": "tonnes", "scope": "scope_3", "ef_uncertainty": 15.0},
    "waste_incineration": {"factor": 21.0, "unit": "tonnes", "scope": "scope_3", "ef_uncertainty": 15.0},
    "waste_composted": {"factor": 8.95, "unit": "tonnes", "scope": "scope_3", "ef_uncertainty": 20.0},
    
    # Water
    "water_supply": {"factor": 0.149, "unit": "m3", "scope": "scope_3", "ef_uncertainty": 10.0},
    "water_treatment": {"factor": 0.272, "unit": "m3", "scope": "scope_3", "ef_uncertainty": 10.0},
    
    # Energy
    "electricity_grid": {"factor": 0.233, "unit": "kWh", "scope": "scope_2", "ef_uncertainty": 5.0},
    "electricity_renewable": {"factor": 0.0, "unit": "kWh", "scope": "scope_2", "ef_uncertainty": 0.0},
    "natural_gas": {"factor": 0.185, "unit": "kWh", "scope": "scope_1", "ef_uncertainty": 5.0},
    "diesel_stationary": {"factor": 2.51, "unit": "litres", "scope": "scope_1", "ef_uncertainty": 5.0},
    "lpg": {"factor": 1.56, "unit": "litres", "scope": "scope_1", "ef_uncertainty": 5.0},
    
    # Transport
    "diesel_mobile": {"factor": 2.51, "unit": "litres", "scope": "scope_1", "ef_uncertainty": 5.0},
    "petrol_mobile": {"factor": 2.19, "unit": "litres", "scope": "scope_1", "ef_uncertainty": 5.0},
    "van_diesel": {"factor": 0.251, "unit": "km", "scope": "scope_1", "ef_uncertainty": 10.0},
    "hgv_rigid": {"factor": 0.811, "unit": "km", "scope": "scope_1", "ef_uncertainty": 10.0},
    "hgv_articulated": {"factor": 0.961, "unit": "km", "scope": "scope_1", "ef_uncertainty": 10.0},
    
    # Business Travel
    "flight_domestic": {"factor": 0.246, "unit": "km", "scope": "scope_3", "ef_uncertainty": 15.0},
    "flight_short_haul": {"factor": 0.149, "unit": "km", "scope": "scope_3", "ef_uncertainty": 15.0},
    "flight_long_haul": {"factor": 0.191, "unit": "km", "scope": "scope_3", "ef_uncertainty": 15.0},
    "rail": {"factor": 0.035, "unit": "km", "scope": "scope_3", "ef_uncertainty": 10.0},
    "taxi": {"factor": 0.208, "unit": "km", "scope": "scope_3", "ef_uncertainty": 15.0},
    
    # Legacy mappings
    "electricity": {"factor": 0.233, "unit": "kWh", "scope": "scope_2", "ef_uncertainty": 5.0},
    "business_travel": {"factor": 0.15, "unit": "km", "scope": "scope_3", "ef_uncertainty": 20.0}
}
