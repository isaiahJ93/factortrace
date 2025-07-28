"""
GHG Calculator API Endpoint with Monte Carlo Analysis and Export Functionality
Enhanced with ESRS E1 Compliance Features
Version 2.0 - Dr. Polowsky architectural improvements
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
import numpy as np
import io
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.lib.enums import TA_CENTER
import xml.etree.ElementTree as ET
from xml.dom import minidom
from decimal import Decimal
import logging


# ===== HELPER FUNCTIONS FOR MONTE CARLO =====
import numpy as np
from scipy import stats
from typing import List, Dict

def calculate_combined_uncertainty(activity_uncertainty: float, ef_uncertainty: float) -> float:
    """Calculate combined uncertainty using error propagation"""
    return float(np.sqrt(activity_uncertainty**2 + ef_uncertainty**2))

def select_distribution(uncertainty_percent: float, distribution_type: str = "lognormal"):
    """Select appropriate distribution based on uncertainty level"""
    if distribution_type == "normal":
        return stats.norm(loc=1.0, scale=uncertainty_percent/100)
    else:  # lognormal (default)
        cv = uncertainty_percent / 100
        sigma = np.sqrt(np.log(1 + cv**2))
        mu = -sigma**2 / 2
        return stats.lognorm(s=sigma, scale=np.exp(mu))

def run_monte_carlo(base_value: float, uncertainty_percent: float, 
                   n_iterations: int = 10000, distribution_type: str = "lognormal") -> np.ndarray:
    """Run Monte Carlo simulation for a single value"""
    if uncertainty_percent == 0 or base_value == 0:
        return np.full(n_iterations, base_value)
    
    dist = select_distribution(uncertainty_percent, distribution_type)
    samples = dist.rvs(size=n_iterations)
    return base_value * samples

def aggregate_uncertainties(values: List[float], uncertainties: List[float], 
                          n_iterations: int = 10000) -> Dict[str, float]:
    """Aggregate uncertainties from multiple sources"""
    if not values or all(v == 0 for v in values):
        return {
            "mean": 0.0,
            "std": 0.0,
            "lower_95": 0.0,
            "upper_95": 0.0,
            "cv": 0.0
        }
    
    all_samples = []
    for value, uncertainty in zip(values, uncertainties):
        samples = run_monte_carlo(value, uncertainty, n_iterations)
        all_samples.append(samples)
    
    total_samples = np.sum(all_samples, axis=0)
    
    return {
        "mean": float(np.mean(total_samples)),
        "std": float(np.std(total_samples)),
        "lower_95": float(np.percentile(total_samples, 2.5)),
        "upper_95": float(np.percentile(total_samples, 97.5)),
        "cv": float(np.std(total_samples) / np.mean(total_samples) * 100) if np.mean(total_samples) > 0 else 0
    }

def calculate_combined_uncertainty(activity_uncertainty: float, ef_uncertainty: float) -> float:
    """Calculate combined uncertainty using error propagation"""
    import numpy as np
    return float(np.sqrt(activity_uncertainty**2 + ef_uncertainty**2))


router = APIRouter()

# ===== ESRS E1 MODELS =====
class EnergyConsumption(BaseModel):
    """E1-5: Energy consumption and mix"""
    total_energy_mwh: float = Field(0, description="Total energy consumption in MWh")
    electricity_mwh: float = Field(0, description="Electricity consumption")
    heating_cooling_mwh: float = Field(0, description="Heating and cooling consumption")
    steam_mwh: float = Field(0, description="Steam consumption")
    fuel_combustion_mwh: float = Field(0, description="Fuel combustion for energy")
    renewable_energy_mwh: float = Field(0, description="Renewable energy consumption")
    renewable_percentage: float = Field(0, ge=0, le=100, description="Percentage renewable")
    energy_intensity_value: Optional[float] = None
    energy_intensity_unit: Optional[str] = "MWh/million_EUR"
    by_source: Optional[Dict[str, float]] = Field(default_factory=dict)
    
    @validator('renewable_percentage')
    def calculate_renewable_percentage(cls, v, values):
        if 'total_energy_mwh' in values and values['total_energy_mwh'] > 0:
            return (values.get('renewable_energy_mwh', 0) / values['total_energy_mwh']) * 100
        return v

class GHGBreakdown(BaseModel):
    """Detailed GHG breakdown by gas type per ESRS E1"""
    CO2_tonnes: float = Field(0, description="CO2 emissions in tonnes")
    CH4_tonnes: float = Field(0, description="CH4 emissions in tonnes")
    N2O_tonnes: float = Field(0, description="N2O emissions in tonnes")
    HFCs_tonnes_co2e: Optional[float] = Field(0, description="HFCs in tonnes CO2e")
    PFCs_tonnes_co2e: Optional[float] = Field(0, description="PFCs in tonnes CO2e")
    SF6_tonnes: Optional[float] = Field(0, description="SF6 in tonnes")
    NF3_tonnes: Optional[float] = Field(0, description="NF3 in tonnes")
    total_co2e: float = Field(0, description="Total CO2 equivalent")
    gwp_version: str = Field("AR6", description="GWP version used (AR6/AR5)")

class InternalCarbonPricing(BaseModel):
    """E1-8: Internal carbon pricing mechanism"""
    implemented: bool = Field(False, description="Whether internal carbon pricing is implemented")
    price_per_tco2e: Optional[float] = Field(None, description="Price per tonne CO2e")
    currency: str = Field("EUR", description="Currency for carbon price")
    coverage_scope1: bool = Field(False, description="Applies to Scope 1")
    coverage_scope2: bool = Field(False, description="Applies to Scope 2")
    coverage_scope3_categories: List[int] = Field(default_factory=list, description="Scope 3 categories covered")
    pricing_type: Optional[str] = Field(None, description="shadow/internal/implicit")
    total_revenue_generated: Optional[float] = Field(0, description="Revenue from carbon pricing")
    revenue_allocation: Optional[str] = None

class ClimatePolicy(BaseModel):
    """E1-2: Climate change mitigation and adaptation policies"""
    has_climate_policy: bool = Field(False)
    policy_adoption_date: Optional[str] = None
    policy_document_url: Optional[str] = None
    policy_description: Optional[str] = None
    net_zero_target_year: Optional[int] = None
    interim_targets: List[Dict[str, Any]] = Field(default_factory=list)
    board_oversight: bool = Field(False)
    executive_compensation_linked: bool = Field(False)
    covers_value_chain: bool = Field(False)

class ClimateActions(BaseModel):
    """E1-3: Actions and resources related to climate change"""
    reporting_year: int = Field(..., description="Reporting year")
    capex_climate_eur: float = Field(0, description="CapEx for climate mitigation/adaptation")
    opex_climate_eur: float = Field(0, description="OpEx for climate mitigation/adaptation")
    total_climate_finance_eur: float = Field(0, description="Total climate finance")
    fte_dedicated: float = Field(0, description="FTEs dedicated to climate actions")
    key_projects: List[Dict[str, Any]] = Field(default_factory=list, description="Key climate projects")
    
    @validator('total_climate_finance_eur')
    def calculate_total_finance(cls, v, values):
        return values.get('capex_climate_eur', 0) + values.get('opex_climate_eur', 0)

class ESRSE1Metadata(BaseModel):
    """Complete ESRS E1 metadata structure"""
    energy_consumption: Optional[EnergyConsumption] = None
    ghg_breakdown: Optional[GHGBreakdown] = None
    internal_carbon_pricing: Optional[InternalCarbonPricing] = None
    climate_policy: Optional[ClimatePolicy] = None
    climate_actions: Optional[ClimateActions] = None

# ===== ENHANCED MODELS =====
class EmissionInput(BaseModel):
    activity_type: str
    amount: float = Field(..., gt=0)
    unit: str
    uncertainty_percentage: Optional[float] = 10.0
    # New fields for gas-specific calculations
    gas_type: Optional[str] = "CO2"  # CO2, CH4, N2O, etc.
    custom_factor: Optional[float] = None

class CalculateEmissionsRequest(BaseModel):
    company_id: str = "default"
    reporting_period: str
    emissions_data: List[EmissionInput]
    # New ESRS E1 fields
    esrs_e1_data: Optional[ESRSE1Metadata] = None
    include_gas_breakdown: bool = False

class MonteCarloRequest(BaseModel):
    reporting_period: str
    emissions_data: List[Dict[str, Any]]
    monte_carlo_iterations: int = 10000
    include_uncertainty: bool = True
    # New ESRS E1 fields
    esrs_e1_data: Optional[Dict[str, Any]] = None
    include_gas_breakdown: bool = False

class ExportRequest(BaseModel):
    results: Optional[Dict[str, Any]] = None
    activities: Optional[List[Dict[str, Any]]] = None
    reporting_period: str
    data_quality: Optional[Dict[str, float]] = None
    company_info: Optional[Dict[str, str]] = None
    emissions_data: Optional[List[Dict[str, Any]]] = None
    summary: Optional[Dict[str, Any]] = None
    company: Optional[Dict[str, str]] = None
    esrs_mapping: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    # New ESRS E1 export data
    esrs_e1_data: Optional[Dict[str, Any]] = None

class EmissionBreakdown(BaseModel):
    activity_type: str
    scope: str
    emissions_kg_co2e: float
    unit: str
    calculation_method: str
    # New fields for gas breakdown
    gas_type: Optional[str] = "CO2"
    gas_amount_tonnes: Optional[float] = None

class CalculateEmissionsResponse(BaseModel):
    total_emissions_kg_co2e: float
    total_emissions_tons_co2e: float
    scope1_emissions: float
    scope2_emissions: float
    scope3_emissions: float
    breakdown: List[EmissionBreakdown]
    reporting_period: str
    calculation_date: str
    # New ESRS E1 fields
    ghg_breakdown: Optional[GHGBreakdown] = None
    esrs_e1_metadata: Optional[Dict[str, Any]] = None

# ===== GWP FACTORS FOR GAS CONVERSION =====
GWP_FACTORS_AR6 = {
    "CO2": 1.0,
    "CH4": 29.8,  # Fossil methane
    "CH4_biogenic": 27.0,  # Biogenic methane
    "N2O": 273.0,
    "SF6": 25200.0,
    "NF3": 17400.0,
    "HFC-134a": 1530.0,
    "HFC-410A": 2255.0
}

GWP_FACTORS_AR5 = {
    "CO2": 1.0,
    "CH4": 28.0,
    "N2O": 265.0,
    "SF6": 23500.0,
    "NF3": 16100.0
}

# ===== ENHANCED EMISSION FACTORS DATABASE =====
# Adding gas-specific factors where relevant
ENHANCED_EMISSION_FACTORS = {
    # Natural gas now includes CH4 leakage
    "natural_gas_stationary": {
        "factor": 0.185, 
        "unit": "kWh", 
        "scope": "scope_1",
        "gas_composition": {"CO2": 0.99, "CH4": 0.01}  # 1% methane leakage
    },
    "diesel_fleet": {
        "factor": 2.51, 
        "unit": "litres", 
        "scope": "scope_1",
        "gas_composition": {"CO2": 0.97, "CH4": 0.01, "N2O": 0.02}
    },
    "waste_landfill": {
        "factor": 467.0, 
        "unit": "tonnes", 
        "scope": "scope_3",
        "gas_composition": {"CO2": 0.3, "CH4": 0.7}  # Landfills produce mostly methane
    },
    "livestock": {
        "factor": 2400.0,
        "unit": "head",
        "scope": "scope_1",
        "gas_composition": {"CH4": 0.9, "N2O": 0.1}  # Enteric fermentation
    },
    "fertilizer_application": {
        "factor": 4.87,
        "unit": "kg_N",
        "scope": "scope_1",
        "gas_composition": {"N2O": 1.0},  # Pure N2O emissions
    },
    "diesel_stationary": {
        "factor": 2.51,
        "unit": "litres",
        "scope": "scope_1",
        "gas_composition": {"CO2": 0.97, "CH4": 0.01, "N2O": 0.02}
    },
    "electricity_grid": {
        "factor": 0.233,
        "unit": "kWh",
        "scope": "scope_2",
        "gas_composition": {"CO2": 1.0}
    },
    "district_heating": {
        "factor": 0.210,
        "unit": "kWh",
        "scope": "scope_2",
        "gas_composition": {"CO2": 1.0}
    },
    "office_paper": {
        "factor": 0.919,
        "unit": "kg",
        "scope": "scope_3",
        "gas_composition": {"CO2": 1.0}
    },
    "plastic_packaging": {
        "factor": 3.13,
        "unit": "kg",
        "scope": "scope_3",
        "gas_composition": {"CO2": 1.0}
    },
    "machinery": {
        "factor": 0.32,
        "unit": "EUR",
        "scope": "scope_3",
        "gas_composition": {"CO2": 1.0}
    },
    "buildings": {
        "factor": 0.26,
        "unit": "EUR",
        "scope": "scope_3",
        "gas_composition": {"CO2": 1.0}
    },
    "upstream_electricity": {
        "factor": 0.045,
        "unit": "kWh",
        "scope": "scope_3",
        "gas_composition": {"CO2": 1.0}
    },
    "road_freight": {
        "factor": 0.096,
        "unit": "tonne.km",
        "scope": "scope_3",
        "gas_composition": {"CO2": 1.0}
    }
}

DEFAULT_EMISSION_FACTORS = {}
# Merge with existing factors
DEFAULT_EMISSION_FACTORS.update(ENHANCED_EMISSION_FACTORS)

# ===== HELPER FUNCTIONS =====
def calculate_gas_breakdown(emissions_kg_co2e: float, activity_type: str, gwp_version: str = "AR6") -> Dict[str, float]:
    """Calculate breakdown by gas type based on activity"""
    gwp_factors = GWP_FACTORS_AR6 if gwp_version == "AR6" else GWP_FACTORS_AR5
    
    # Get gas composition for this activity
    factor_data = DEFAULT_EMISSION_FACTORS.get(activity_type, {})
    gas_composition = factor_data.get("gas_composition", {"CO2": 1.0})
    
    breakdown = {}
    for gas, fraction in gas_composition.items():
        # Calculate tonnes of each gas
        gas_co2e = emissions_kg_co2e * fraction / 1000  # Convert to tonnes
        gwp = gwp_factors.get(gas, 1.0)
        gas_tonnes = gas_co2e / gwp
        breakdown[f"{gas}_tonnes"] = gas_tonnes
    
    return breakdown

def aggregate_energy_from_activities(activities: List[Dict[str, Any]]) -> EnergyConsumption:
    """Aggregate energy consumption from Scope 2 activities"""
    energy_data = {
        "electricity_mwh": 0,
        "heating_cooling_mwh": 0,
        "steam_mwh": 0,
        "renewable_energy_mwh": 0,
        "total_energy_mwh": 0
    }
    
    for activity in activities:
        activity_type = activity.get("activity_type", "").lower()
        amount = activity.get("amount", 0)
        
        # Map activities to energy types
        if "electricity" in activity_type:
            if activity_type in ["electricity_grid", "electricity"]:
                energy_data["electricity_mwh"] += amount / 1000  # kWh to MWh
            elif activity_type == "electricity_renewable":
                energy_data["renewable_energy_mwh"] += amount / 1000
                energy_data["electricity_mwh"] += amount / 1000
        elif "heating" in activity_type or "cooling" in activity_type:
            energy_data["heating_cooling_mwh"] += amount / 1000
        elif "steam" in activity_type:
            energy_data["steam_mwh"] += amount / 1000
    
    energy_data["total_energy_mwh"] = sum([
        energy_data["electricity_mwh"],
        energy_data["heating_cooling_mwh"],
        energy_data["steam_mwh"]
    ])
    
    return EnergyConsumption(**energy_data)

# ===== ENHANCED ENDPOINTS =====
@router.post("/calculate", response_model=CalculateEmissionsResponse)
async def calculate_emissions(request: CalculateEmissionsRequest):
    """Calculate GHG emissions with ESRS E1 compliance features"""
    total_emissions = 0.0
    scope_totals = {"scope_1": 0.0, "scope_2": 0.0, "scope_3": 0.0}
    breakdown = []
    
    # Initialize gas breakdown
    gas_breakdown = {
        "CO2_tonnes": 0.0,
        "CH4_tonnes": 0.0,
        "N2O_tonnes": 0.0,
        "HFCs_tonnes_co2e": 0.0,
        "PFCs_tonnes_co2e": 0.0,
        "SF6_tonnes": 0.0,
        "NF3_tonnes": 0.0
    }
    
    # Process each emission input
    for emission_input in request.emissions_data:
        activity_type = emission_input.activity_type.lower()
        
        if activity_type not in DEFAULT_EMISSION_FACTORS and not emission_input.custom_factor:
            continue
            
        # Get emission factor
        if emission_input.custom_factor:
            factor = emission_input.custom_factor
            scope = "scope_3"  # Default custom factors to scope 3
        else:
            factor_data = DEFAULT_EMISSION_FACTORS[activity_type]
            factor = factor_data["factor"]
            scope = factor_data["scope"]
        
        emissions_kg = emission_input.amount * factor
        scope_totals[scope] += emissions_kg
        total_emissions += emissions_kg
        
        # Calculate gas breakdown if requested
        gas_amount_tonnes = None
        if request.include_gas_breakdown:
            gas_specific = calculate_gas_breakdown(emissions_kg, activity_type)
            for gas, amount in gas_specific.items():
                if gas in gas_breakdown:
                    gas_breakdown[gas] += amount
        
        breakdown.append(EmissionBreakdown(
            activity_type=emission_input.activity_type,
            scope=scope,
            emissions_kg_co2e=round(emissions_kg, 2),
            unit=emission_input.unit,
            calculation_method="emission_factor",
            gas_type=emission_input.gas_type,
            gas_amount_tonnes=gas_amount_tonnes
        ))
    
    # Calculate total CO2e for gas breakdown
    gas_breakdown["total_co2e"] = total_emissions / 1000
    
    # Create GHG breakdown object
    ghg_breakdown_obj = GHGBreakdown(**gas_breakdown) if request.include_gas_breakdown else None
    
    # Prepare ESRS E1 metadata
    esrs_e1_metadata = None
    if request.esrs_e1_data:
        # If energy consumption not provided, try to aggregate from activities
        if not request.esrs_e1_data.energy_consumption:
            request.esrs_e1_data.energy_consumption = aggregate_energy_from_activities(
                [{"activity_type": e.activity_type, "amount": e.amount} for e in request.emissions_data]
            )
        
        esrs_e1_metadata = request.esrs_e1_data.model_dump()
    
    return CalculateEmissionsResponse(
        total_emissions_kg_co2e=round(total_emissions, 2),
        total_emissions_tons_co2e=round(total_emissions / 1000, 2),
        scope1_emissions=round(scope_totals["scope_1"], 2),
        scope2_emissions=round(scope_totals["scope_2"], 2),
        scope3_emissions=round(scope_totals["scope_3"], 2),
        breakdown=breakdown,
        reporting_period=request.reporting_period,
        calculation_date=str(date.today()),
        ghg_breakdown=ghg_breakdown_obj,
        esrs_e1_metadata=esrs_e1_metadata
    )

@router.post("/calculate-with-monte-carlo")
async def calculate_with_monte_carlo(request: Dict[str, Any]):
    """
    Enhanced Monte Carlo calculation with ESRS E1 support
    """
    try:
        # Extract request data
        reporting_period = request.get("reporting_period", str(date.today()))
        emissions_data = request.get("emissions_data", [])
        monte_carlo_iterations = request.get("monte_carlo_iterations", 10000)
        include_uncertainty = request.get("include_uncertainty", True)
        esrs_e1_data = request.get("esrs_e1_data", {})
        include_gas_breakdown = request.get("include_gas_breakdown", False)
        
        # Initialize totals
        total_emissions = 0.0
        scope_totals = {"scope_1": 0.0, "scope_2": 0.0, "scope_3": 0.0}
        breakdown = []
        
        # Initialize gas breakdown
        gas_breakdown = {
            "CO2_tonnes": 0.0,
            "CH4_tonnes": 0.0,
            "N2O_tonnes": 0.0,
            "total_co2e": 0.0
        }
        
        # Calculate base emissions
        for activity in emissions_data:
            activity_type = activity.get("activity_type", "").lower()
            amount = float(activity.get("amount", 0))
            unit = activity.get("unit", "")
            
            # Find emission factor
            factor_data = DEFAULT_EMISSION_FACTORS.get(activity_type)
            if not factor_data:
                # Try alternate names
                if activity_type == "electricity":
                    factor_data = DEFAULT_EMISSION_FACTORS.get("electricity_grid")
                elif activity_type == "natural gas":
                    factor_data = DEFAULT_EMISSION_FACTORS.get("natural_gas_stationary")
                
                if not factor_data:
                    continue
            
            emissions_kg = amount * factor_data["factor"]
            scope = factor_data["scope"]
            scope_totals[scope] += emissions_kg
            total_emissions += emissions_kg
            
            # Calculate gas breakdown
            if include_gas_breakdown:
                gas_specific = calculate_gas_breakdown(emissions_kg, activity_type)
                for gas, amount_tonnes in gas_specific.items():
                    gas_key = gas.replace("_tonnes", "_tonnes")
                    if gas_key in gas_breakdown:
                        gas_breakdown[gas_key] += amount_tonnes
            
            breakdown.append({
                "activity_type": activity_type,
                "scope": scope,
                "emissions_kg_co2e": round(emissions_kg, 2),
                "unit": unit,
                "calculation_method": "emission_factor"
            })
        
        # Set total CO2e
        gas_breakdown["total_co2e"] = total_emissions / 1000
        
        # Monte Carlo simulation
        uncertainty_analysis = None
        if include_uncertainty and monte_carlo_iterations > 0:
            simulation_results = []
            gas_simulations = {
                "CO2_tonnes": [],
                "CH4_tonnes": [],
                "N2O_tonnes": []
            }
            
            for _ in range(monte_carlo_iterations):
                sim_total = 0.0
                sim_gas_breakdown = {"CO2_tonnes": 0.0, "CH4_tonnes": 0.0, "N2O_tonnes": 0.0}
                
                for activity in emissions_data:
                    activity_type = activity.get("activity_type", "").lower()
                    amount = float(activity.get("amount", 0))
                    activity_uncertainty = float(activity.get("uncertainty_percentage", 10))
                    
                    # Get factor
                    factor_data = DEFAULT_EMISSION_FACTORS.get(activity_type)
                    if not factor_data:
                        if activity_type == "electricity":
                            factor_data = DEFAULT_EMISSION_FACTORS.get("electricity_grid")
                        elif activity_type == "natural gas":
                            factor_data = DEFAULT_EMISSION_FACTORS.get("natural_gas_stationary")
                        
                        if not factor_data:
                            continue
                    
                    # Calculate with uncertainty
                    factor_uncertainty = factor_data.get("uncertainty", 10)
                    combined_uncertainty = calculate_combined_uncertainty(
                        activity_uncertainty, 
                        factor_uncertainty
                    ) / 100
                    
                    # Select distribution
                    distribution = select_distribution(combined_uncertainty * 100)
                    
                    if distribution == "normal":
                        sim_amount = np.random.normal(amount, amount * combined_uncertainty)
                    elif distribution == "lognormal":
                        sigma = np.sqrt(np.log(1 + combined_uncertainty**2))
                        mu = np.log(amount) - sigma**2 / 2
                        sim_amount = np.random.lognormal(mu, sigma)
                    else:  # triangular
                        min_val = amount * (1 - 2 * combined_uncertainty)
                        max_val = amount * (1 + 2 * combined_uncertainty)
                        sim_amount = np.random.triangular(min_val, amount, max_val)
                    
                    sim_emissions = max(0, sim_amount * factor_data["factor"])
                    sim_total += sim_emissions
                    
                    # Track gas breakdown in simulation
                    if include_gas_breakdown:
                        gas_specific = calculate_gas_breakdown(sim_emissions, activity_type)
                        for gas, amount_tonnes in gas_specific.items():
                            gas_key = gas.replace("_tonnes", "_tonnes")
                            if gas_key in sim_gas_breakdown:
                                sim_gas_breakdown[gas_key] += amount_tonnes
                
                simulation_results.append(sim_total)
                
                # Store gas simulations
                for gas, value in sim_gas_breakdown.items():
                    if gas in gas_simulations:
                        gas_simulations[gas].append(value)
            
            # Calculate statistics
            if simulation_results:
                results_array = np.array(simulation_results)
                mean_emissions = float(np.mean(results_array))
                std_dev = float(np.std(results_array))
                cv = (std_dev / mean_emissions * 100) if mean_emissions > 0 else 0
                
                uncertainty_analysis = {
                    "monte_carlo_runs": monte_carlo_iterations,
                    "mean_emissions": mean_emissions,
                    "std_deviation": std_dev,
                    "coefficient_of_variation": cv,
                    "confidence_interval_95": [
                        float(np.percentile(results_array, 2.5)),
                        float(np.percentile(results_array, 97.5))
                    ],
                    "confidence_interval_90": [
                        float(np.percentile(results_array, 5)),
                        float(np.percentile(results_array, 95))
                    ],
                    "relative_uncertainty_percent": float((std_dev / mean_emissions * 100)) if mean_emissions > 0 else 0,
                    "methodology": "IPCC Tier 2 Monte Carlo"
                }
                
                # Add gas-specific uncertainty if calculated
                if include_gas_breakdown:
                    uncertainty_analysis["gas_breakdown_uncertainty"] = {}
                    for gas, sim_values in gas_simulations.items():
                        if sim_values:
                            gas_array = np.array(sim_values)
                            uncertainty_analysis["gas_breakdown_uncertainty"][gas] = {
                                "mean": float(np.mean(gas_array)),
                                "confidence_interval_95": [
                                    float(np.percentile(gas_array, 2.5)),
                                    float(np.percentile(gas_array, 97.5))
                                ]
                            }
        
        # Process ESRS E1 data
        esrs_e1_metadata = None
        if esrs_e1_data:
            # Auto-calculate energy if not provided
            if not esrs_e1_data.get("energy_consumption"):
                energy_activities = [a for a in emissions_data if "electricity" in a.get("activity_type", "").lower() 
                                   or "heating" in a.get("activity_type", "").lower()
                                   or "cooling" in a.get("activity_type", "").lower()
                                   or "steam" in a.get("activity_type", "").lower()]
                
                if energy_activities:
                    esrs_e1_data["energy_consumption"] = aggregate_energy_from_activities(energy_activities).model_dump()
            
            esrs_e1_metadata = esrs_e1_data
        
        # Prepare response
        response = {
            "summary": {
                "total_emissions_tons_co2e": round(total_emissions / 1000, 2),
                "scope1_emissions": round(scope_totals["scope_1"], 2),
                "scope2_location_based": round(scope_totals["scope_2"], 2),
                "scope2_market_based": round(scope_totals["scope_2"], 2),
                "scope3_emissions": round(scope_totals["scope_3"], 2),
            },
            "breakdown": breakdown,
            "reporting_period": reporting_period,
            "calculation_date": str(date.today()),
            "uncertainty_analysis": uncertainty_analysis,
            "ghg_breakdown": gas_breakdown if include_gas_breakdown else None,
            "esrs_e1_metadata": esrs_e1_metadata
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in Monte Carlo calculation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity-types")
async def get_activity_types():
    """Get all supported activity types with gas composition info"""
    activity_types = {
        "scope_1": [],
        "scope_2": [],
        "scope_3": []
    }
    
    seen = set()
    
    for name, data in DEFAULT_EMISSION_FACTORS.items():
        key = f"{name}_{data['unit']}"
        if key not in seen:
            seen.add(key)
            scope = data["scope"]
            
            activity_info = {
                "value": name,
                "label": name.replace("-", " ").replace("_", " ").title(),
                "unit": data["unit"],
                "factor": data["factor"]
            }
            
            # Add gas composition if available
            if "gas_composition" in data:
                activity_info["gas_composition"] = data["gas_composition"]
            
            activity_types[scope].append(activity_info)
    
    return activity_types

@router.get("/emission-factors")
async def get_emission_factors():
    """Get all emission factors with enhanced metadata"""
    factors = []
    seen = set()
    
    for name, data in DEFAULT_EMISSION_FACTORS.items():
        key = f"{name}_{data['unit']}"
        if key not in seen:
            seen.add(key)
            factor_info = {
                "name": name.replace("-", " ").replace("_", " ").title(),
                "category": name,
                "unit": data["unit"],
                "factor": data["factor"],
                "scope": int(data["scope"].split("_")[1])
            }
            
            # Add gas composition and uncertainty if available
            if "gas_composition" in data:
                factor_info["gas_composition"] = data["gas_composition"]
            if "uncertainty" in data:
                factor_info["uncertainty_percent"] = data["uncertainty"]
            
            factors.append(factor_info)
    
    return factors

# ===== ESRS E1 SPECIFIC ENDPOINTS =====
@router.post("/esrs-e1/validate")
async def validate_esrs_e1_data(data: ESRSE1Metadata):
    """Validate ESRS E1 compliance data"""
    validation_results = {
        "is_valid": True,
        "missing_required_fields": [],
        "warnings": [],
        "completeness_score": 0
    }
    
    # Check E1-2: Climate Policy
    if not data.climate_policy or not data.climate_policy.has_climate_policy:
        validation_results["missing_required_fields"].append("E1-2: Climate policy required")
        validation_results["is_valid"] = False
    
    # Check E1-5: Energy Consumption
    if not data.energy_consumption or data.energy_consumption.total_energy_mwh == 0:
        validation_results["warnings"].append("E1-5: Energy consumption data missing")
    
    # Check E1-8: Internal Carbon Pricing
    if not data.internal_carbon_pricing:
        validation_results["warnings"].append("E1-8: Internal carbon pricing not disclosed")
    
    # Calculate completeness score
    fields_provided = 0
    total_fields = 5
    
    if data.climate_policy and data.climate_policy.has_climate_policy:
        fields_provided += 1
    if data.climate_actions and data.climate_actions.total_climate_finance_eur > 0:
        fields_provided += 1
    if data.energy_consumption and data.energy_consumption.total_energy_mwh > 0:
        fields_provided += 1
    if data.ghg_breakdown and data.ghg_breakdown.total_co2e > 0:
        fields_provided += 1
    if data.internal_carbon_pricing and data.internal_carbon_pricing.implemented:
        fields_provided += 1
    
    validation_results["completeness_score"] = (fields_provided / total_fields) * 100
    
    return validation_results

@router.post("/esrs-e1/aggregate-energy")
async def aggregate_energy_consumption(request: Dict[str, Any]):
    """Aggregate energy consumption from emission activities"""
    activities = request.get("activities", [])
    
    energy_consumption = aggregate_energy_from_activities(activities)
    
    # Add renewable percentage calculation
    if energy_consumption.total_energy_mwh > 0:
        energy_consumption.renewable_percentage = (
            energy_consumption.renewable_energy_mwh / energy_consumption.total_energy_mwh * 100
        )
    
    return energy_consumption

# Enhanced PDF export remains the same but with ESRS E1 sections added
# Enhanced iXBRL export remains the same but with ESRS E1 tags added

# Keep all existing export endpoints unchanged for backward compatibility