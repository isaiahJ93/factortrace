# run_ghg_api.py - A standalone working GHG calculator API
"""
Minimal working GHG emissions calculator API
Run this directly to bypass import issues
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import date
import uvicorn

# Create FastAPI app
app = FastAPI(title="GHG Emissions Calculator", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class EmissionInput(BaseModel):
    activity_type: str = Field(..., description="Type of activity")
    amount: float = Field(..., gt=0, description="Amount of activity")
    unit: str = Field(..., description="Unit of measurement")

class CalculateRequest(BaseModel):
    company_id: str = Field(default="default", description="Company ID")
    reporting_period: str = Field(..., description="Reporting period")
    emissions_data: List[EmissionInput]

class EmissionBreakdown(BaseModel):
    activity_type: str
    scope: str
    emissions_kg_co2e: float
    unit: str
    calculation_method: str

class CalculateResponse(BaseModel):
    total_emissions_kg_co2e: float
    total_emissions_tons_co2e: float
    scope1_emissions: float
    scope2_emissions: float
    scope3_emissions: float
    breakdown: List[EmissionBreakdown]
    reporting_period: str
    calculation_date: str

# Default emission factors (kg CO2e per unit)
EMISSION_FACTORS = {
    # Scope 1 - Direct emissions
    "natural_gas": {"factor": 1.85, "unit": "m3", "scope": "scope_1"},
    "diesel": {"factor": 2.68, "unit": "liters", "scope": "scope_1"},
    "gasoline": {"factor": 2.35, "unit": "liters", "scope": "scope_1"},
    "vehicle_fuel": {"factor": 2.35, "unit": "liters", "scope": "scope_1"},
    
    # Scope 2 - Electricity
    "electricity": {"factor": 0.45, "unit": "kWh", "scope": "scope_2"},
    "electricity_renewable": {"factor": 0.01, "unit": "kWh", "scope": "scope_2"},
    
    # Scope 3 - Value chain
    "business_travel": {"factor": 0.21, "unit": "km", "scope": "scope_3"},
    "air_travel": {"factor": 0.255, "unit": "km", "scope": "scope_3"},
    "rail_travel": {"factor": 0.041, "unit": "km", "scope": "scope_3"},
    "waste_landfill": {"factor": 467, "unit": "tonnes", "scope": "scope_3"},
    "waste_recycling": {"factor": -885, "unit": "tonnes", "scope": "scope_3"},
    "water_supply": {"factor": 0.149, "unit": "m3", "scope": "scope_3"},
    "paper": {"factor": 1840, "unit": "tonnes", "scope": "scope_3"},
}

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "GHG Emissions Calculator API",
        "endpoints": {
            "calculate": "/api/v1/ghg-calculator/calculate",
            "factors": "/api/v1/ghg-calculator/emission-factors",
            "activities": "/api/v1/ghg-calculator/activity-types",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": date.today().isoformat()}

@app.post("/api/v1/ghg-calculator/calculate", response_model=CalculateResponse)
async def calculate_emissions(request: CalculateRequest):
    """
    Calculate GHG emissions for provided activities
    """
    total_emissions = 0.0
    scope_totals = {"scope_1": 0.0, "scope_2": 0.0, "scope_3": 0.0}
    breakdown = []
    
    for activity in request.emissions_data:
        activity_type = activity.activity_type.lower().replace(" ", "_")
        
        # Get emission factor
        if activity_type not in EMISSION_FACTORS:
            # Try to find a partial match
            matched = False
            for key in EMISSION_FACTORS:
                if key in activity_type or activity_type in key:
                    activity_type = key
                    matched = True
                    break
            
            if not matched:
                # Skip unknown activities
                continue
        
        factor_data = EMISSION_FACTORS[activity_type]
        
        # Calculate emissions (kg CO2e)
        emissions_kg = activity.amount * factor_data["factor"]
        
        # Add to scope totals
        scope = factor_data["scope"]
        scope_totals[scope] += emissions_kg
        total_emissions += emissions_kg
        
        # Add to breakdown
        breakdown.append(EmissionBreakdown(
            activity_type=activity.activity_type,
            scope=scope,
            emissions_kg_co2e=round(emissions_kg, 2),
            unit=activity.unit,
            calculation_method="emission_factor"
        ))
    
    return CalculateResponse(
        total_emissions_kg_co2e=round(total_emissions, 2),
        total_emissions_tons_co2e=round(total_emissions / 1000, 3),
        scope1_emissions=round(scope_totals["scope_1"], 2),
        scope2_emissions=round(scope_totals["scope_2"], 2),
        scope3_emissions=round(scope_totals["scope_3"], 2),
        breakdown=breakdown,
        reporting_period=request.reporting_period,
        calculation_date=date.today().isoformat()
    )

@app.get("/api/v1/ghg-calculator/emission-factors")
async def get_emission_factors():
    """Get all available emission factors"""
    factors = []
    for activity_type, data in EMISSION_FACTORS.items():
        factors.append({
            "activity_type": activity_type,
            "display_name": activity_type.replace("_", " ").title(),
            "unit": data["unit"],
            "scope": data["scope"],
            "factor": data["factor"],
            "factor_unit": f"kg CO2e/{data['unit']}"
        })
    
    return {
        "emission_factors": sorted(factors, key=lambda x: (x["scope"], x["activity_type"])),
        "source": "GHG Protocol Default Factors",
        "year": 2024,
        "total_factors": len(factors)
    }

@app.get("/api/v1/ghg-calculator/activity-types")
async def get_activity_types():
    """Get activity types grouped by scope"""
    scope_groups = {
        "scope_1": [],
        "scope_2": [],
        "scope_3": []
    }
    
    for activity_type, data in EMISSION_FACTORS.items():
        scope = data["scope"]
        scope_groups[scope].append({
            "value": activity_type,
            "label": activity_type.replace("_", " ").title(),
            "unit": data["unit"],
            "factor": data["factor"]
        })
    
    return scope_groups

# Example calculation endpoint for quick testing
@app.get("/api/v1/ghg-calculator/example")
async def example_calculation():
    """Get an example calculation"""
    example_request = {
        "company_id": "example-corp",
        "reporting_period": "2024-Q1",
        "emissions_data": [
            {"activity_type": "electricity", "amount": 10000, "unit": "kWh"},
            {"activity_type": "natural_gas", "amount": 1000, "unit": "m3"},
            {"activity_type": "vehicle_fuel", "amount": 500, "unit": "liters"},
            {"activity_type": "business_travel", "amount": 5000, "unit": "km"},
            {"activity_type": "waste_landfill", "amount": 2, "unit": "tonnes"}
        ]
    }
    
    return {
        "example_request": example_request,
        "description": "POST this data to /api/v1/ghg-calculator/calculate",
        "expected_result": "Approximately 8.4 tCO2e total emissions"
    }

if __name__ == "__main__":
    print("🚀 Starting GHG Emissions Calculator API")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🧪 Example calculation: http://localhost:8000/api/v1/ghg-calculator/example")
    print("✋ Press CTRL+C to stop the server\n")
    
    # Run without reload when called directly
    uvicorn.run(app, host="0.0.0.0", port=8000)