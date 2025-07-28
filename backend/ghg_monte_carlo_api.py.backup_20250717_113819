# ghg_monte_carlo_api_fixed.py - Corrected Monte Carlo GHG Calculator
"""
Fixed version with proper uncertainty calculations
Replace your current ghg_monte_carlo_api.py with this
"""
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from datetime import date
from enum import Enum
import uvicorn
from scipy.stats import lognorm, norm

app = FastAPI(
    title="GHG Calculator with Monte Carlo - Fixed",
    version="3.1.0",
    description="Corrected Monte Carlo uncertainty calculations"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class UncertaintyDistribution(str, Enum):
    NORMAL = "normal"
    LOGNORMAL = "lognormal"

class EmissionActivity(BaseModel):
    activity_type: str
    amount: float = Field(..., gt=0)
    unit: str
    uncertainty_percentage: float = Field(default=10.0, ge=0, le=100)
    data_quality: str = Field(default="estimated")

class MonteCarloRequest(BaseModel):
    reporting_period: str
    emissions_data: List[EmissionActivity]
    monte_carlo_iterations: int = Field(default=10000, ge=1000, le=100000)
    include_uncertainty: bool = Field(default=True)

# Emission factors with uncertainty
EMISSION_FACTORS = {
    "electricity": {
        "factor": 0.45,  # kg CO2e/kWh
        "unit": "kWh", 
        "scope": "scope_2",
        "ef_uncertainty": 10.0  # ±10%
    },
    "natural_gas": {
        "factor": 1.85,  # kg CO2e/m3
        "unit": "m3", 
        "scope": "scope_1",
        "ef_uncertainty": 5.0   # ±5%
    },
    "diesel": {
        "factor": 2.68,
        "unit": "liters", 
        "scope": "scope_1",
        "ef_uncertainty": 3.0
    },
    "vehicle_fuel": {
        "factor": 2.35,
        "unit": "liters",
        "scope": "scope_1", 
        "ef_uncertainty": 3.0
    },
    "business_travel": {
        "factor": 0.21,
        "unit": "km", 
        "scope": "scope_3",
        "ef_uncertainty": 20.0  # ±20%
    },
    "waste_landfill": {
        "factor": 0.467,  # kg CO2e/kg (not tonnes!)
        "unit": "tonnes", 
        "scope": "scope_3",
        "ef_uncertainty": 30.0
    }
}

def calculate_monte_carlo_uncertainty(
    base_emissions: float,
    activity_uncertainty: float,  # percentage
    ef_uncertainty: float,        # percentage
    n_iterations: int = 10000
) -> Dict:
    """
    Correctly calculate uncertainty using Monte Carlo
    """
    # Convert percentages to fractions
    activity_cv = activity_uncertainty / 100
    ef_cv = ef_uncertainty / 100
    
    # Combined uncertainty (root sum of squares for independent variables)
    combined_cv = np.sqrt(activity_cv**2 + ef_cv**2)
    
    # For lognormal distribution
    if combined_cv > 0:
        sigma = np.sqrt(np.log(combined_cv**2 + 1))
        mu = np.log(base_emissions) - sigma**2 / 2
        
        # Generate samples
        samples = np.random.lognormal(mu, sigma, n_iterations)
    else:
        # No uncertainty
        samples = np.full(n_iterations, base_emissions)
    
    # Calculate statistics
    return {
        "mean": float(np.mean(samples)),
        "std_dev": float(np.std(samples)),
        "confidence_interval_95": [
            float(np.percentile(samples, 2.5)),
            float(np.percentile(samples, 97.5))
        ],
        "confidence_interval_90": [
            float(np.percentile(samples, 5)),
            float(np.percentile(samples, 95))
        ],
        "cv_percent": float(combined_cv * 100),
        "samples": samples  # Keep for aggregation
    }

@app.post("/api/v1/calculate-with-monte-carlo")
async def calculate_with_monte_carlo(request: MonteCarloRequest):
    """Calculate emissions with proper Monte Carlo uncertainty"""
    
    total_emissions = 0.0
    scope_totals = {"scope_1": 0.0, "scope_2": 0.0, "scope_3": 0.0}
    breakdown = []
    all_samples = []
    
    for activity in request.emissions_data:
        # Get emission factor
        activity_type_key = activity.activity_type.lower().replace(" ", "_")
        factor_data = EMISSION_FACTORS.get(
            activity_type_key,
            {"factor": 1.0, "unit": activity.unit, "scope": "scope_3", "ef_uncertainty": 30.0}
        )
        
        # Adjust for units (e.g., waste in tonnes but factor in kg)
        amount = activity.amount
        if activity_type_key == "waste_landfill" and activity.unit == "tonnes":
            amount = activity.amount * 1000  # Convert tonnes to kg
        
        # Base calculation
        base_emissions = amount * factor_data["factor"]
        scope = factor_data["scope"]
        scope_totals[scope] += base_emissions
        total_emissions += base_emissions
        
        # Monte Carlo uncertainty
        if request.include_uncertainty:
            mc_result = calculate_monte_carlo_uncertainty(
                base_emissions=base_emissions,
                activity_uncertainty=activity.uncertainty_percentage,
                ef_uncertainty=factor_data["ef_uncertainty"],
                n_iterations=request.monte_carlo_iterations
            )
            
            # Keep samples for total uncertainty
            all_samples.append(mc_result["samples"])
            
            breakdown.append({
                "activity_type": activity.activity_type,
                "scope": scope,
                "amount": activity.amount,
                "unit": activity.unit,
                "emission_factor": factor_data["factor"],
                "base_emissions_kg_co2e": round(base_emissions, 2),
                "uncertainty_analysis": {
                    "mean": round(mc_result["mean"], 2),
                    "std_dev": round(mc_result["std_dev"], 2),
                    "confidence_interval_95": [
                        round(mc_result["confidence_interval_95"][0], 2),
                        round(mc_result["confidence_interval_95"][1], 2)
                    ],
                    "confidence_interval_90": [
                        round(mc_result["confidence_interval_90"][0], 2),
                        round(mc_result["confidence_interval_90"][1], 2)
                    ],
                    "combined_uncertainty_percent": round(mc_result["cv_percent"], 1)
                },
                "data_quality": activity.data_quality
            })
        else:
            breakdown.append({
                "activity_type": activity.activity_type,
                "scope": scope,
                "amount": activity.amount,
                "unit": activity.unit,
                "emission_factor": factor_data["factor"],
                "base_emissions_kg_co2e": round(base_emissions, 2)
            })
    
    # Calculate total uncertainty
    if request.include_uncertainty and all_samples:
        # Sum samples across all activities
        total_samples = np.sum(all_samples, axis=0)
        
        total_uncertainty = {
            "mean": round(float(np.mean(total_samples)), 2),
            "std_dev": round(float(np.std(total_samples)), 2),
            "confidence_interval_95": [
                round(float(np.percentile(total_samples, 2.5)), 2),
                round(float(np.percentile(total_samples, 97.5)), 2)
            ],
            "confidence_interval_90": [
                round(float(np.percentile(total_samples, 5)), 2),
                round(float(np.percentile(total_samples, 95)), 2)
            ],
            "relative_uncertainty_percent": round(
                float(np.std(total_samples) / np.mean(total_samples) * 100), 1
            ) if np.mean(total_samples) > 0 else 0
        }
    else:
        total_uncertainty = None
    
    # Scope 2 dual reporting
    scope2_location = scope_totals["scope_2"]
    scope2_market = scope2_location * 1.44  # Simplified market factor
    
    return {
        "summary": {
            "total_emissions_kg_co2e": round(total_emissions, 2),
            "total_emissions_tons_co2e": round(total_emissions / 1000, 3),
            "scope1_emissions": round(scope_totals["scope_1"], 2),
            "scope2_location_based": round(scope2_location, 2),
            "scope2_market_based": round(scope2_market, 2),
            "scope3_emissions": round(scope_totals["scope_3"], 2)
        },
        "uncertainty_analysis": total_uncertainty,
        "breakdown": breakdown,
        "metadata": {
            "reporting_period": request.reporting_period,
            "calculation_date": date.today().isoformat(),
            "monte_carlo_iterations": request.monte_carlo_iterations if request.include_uncertainty else 0,
            "includes_uncertainty": request.include_uncertainty
        }
    }

@app.get("/api/v1/test-monte-carlo")
async def test_monte_carlo():
    """Test Monte Carlo with realistic values"""
    
    # Test case: 1000 kg CO2e with 10% activity uncertainty and 15% EF uncertainty
    base = 1000.0
    activity_unc = 10.0
    ef_unc = 15.0
    
    result = calculate_monte_carlo_uncertainty(
        base_emissions=base,
        activity_uncertainty=activity_unc,
        ef_uncertainty=ef_unc,
        n_iterations=50000
    )
    
    return {
        "test_case": {
            "base_emissions": base,
            "activity_uncertainty": f"±{activity_unc}%",
            "ef_uncertainty": f"±{ef_unc}%",
            "combined_uncertainty": f"±{result['cv_percent']:.1f}%"
        },
        "monte_carlo_results": {
            "mean": round(result["mean"], 1),
            "std_dev": round(result["std_dev"], 1),
            "confidence_interval_95": [
                round(result["confidence_interval_95"][0], 1),
                round(result["confidence_interval_95"][1], 1)
            ],
            "confidence_interval_90": [
                round(result["confidence_interval_90"][0], 1),
                round(result["confidence_interval_90"][1], 1)
            ]
        },
        "interpretation": {
            "message": "With 95% confidence, emissions are between:",
            "range": f"{result['confidence_interval_95'][0]:.0f} - {result['confidence_interval_95'][1]:.0f} kg CO2e",
            "relative_range": f"{result['confidence_interval_95'][0]/base:.1%} - {result['confidence_interval_95'][1]/base:.1%} of base value"
        }
    }

@app.get("/")
async def root():
    return {
        "message": "GHG Calculator with Corrected Monte Carlo",
        "version": "3.1.0",
        "changes": "Fixed uncertainty calculations - now showing realistic ranges",
        "endpoints": {
            "calculate": "/api/v1/calculate-with-monte-carlo",
            "test": "/api/v1/test-monte-carlo",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting FIXED GHG Calculator with Monte Carlo")
    print("✅ Uncertainty calculations now show realistic ranges")
    print("📊 API Documentation: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)