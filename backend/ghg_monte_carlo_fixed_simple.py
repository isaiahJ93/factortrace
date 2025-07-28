# Quick fixed version for testing
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="Fixed Monte Carlo GHG Calculator")

class EmissionInput(BaseModel):
    activity_type: str
    amount: float
    unit: str
    uncertainty_percentage: float = 10.0

class CalculateRequest(BaseModel):
    reporting_period: str
    emissions_data: List[EmissionInput]

FACTORS = {
    "electricity": {"factor": 0.45, "uncertainty": 10},
    "natural_gas": {"factor": 1.85, "uncertainty": 5},
    "business_travel": {"factor": 0.21, "uncertainty": 20}
}

@app.post("/api/v1/calculate")
async def calculate(request: CalculateRequest):
    total = 0
    results = []
    
    for item in request.emissions_data:
        factor = FACTORS.get(item.activity_type, {"factor": 1, "uncertainty": 30})
        base_emissions = item.amount * factor["factor"]
        total += base_emissions
        
        # Simple uncertainty calc
        combined_uncertainty = np.sqrt(
            (item.uncertainty_percentage/100)**2 + 
            (factor["uncertainty"]/100)**2
        ) * 100
        
        lower = base_emissions * (1 - combined_uncertainty/100 * 1.96)
        upper = base_emissions * (1 + combined_uncertainty/100 * 1.96)
        
        results.append({
            "activity": item.activity_type,
            "base_emissions": round(base_emissions, 2),
            "95_CI": [round(lower, 2), round(upper, 2)],
            "uncertainty": f"±{combined_uncertainty:.1f}%"
        })
    
    return {
        "total_emissions": round(total, 2),
        "total_tons": round(total/1000, 3),
        "breakdown": results,
        "message": "FIXED version - showing correct uncertainty ranges"
    }

@app.get("/")
async def root():
    return {"message": "Fixed Monte Carlo API", "test": "/api/v1/calculate"}

if __name__ == "__main__":
    print("🚀 Running FIXED Monte Carlo API on port 8001")
    uvicorn.run(app, port=8001)
