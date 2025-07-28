"""ESRS E1 specific schemas for enhanced GHG reporting"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import date
from decimal import Decimal

class EnergyConsumption(BaseModel):
    """E1-5: Energy consumption breakdown"""
    total_energy_mwh: float = Field(..., description="Total energy consumption")
    electricity_mwh: float = Field(0, description="Electricity consumption")
    heating_cooling_mwh: float = Field(0, description="Heating/cooling consumption")
    fuel_mwh: float = Field(0, description="Fuel consumption")
    renewable_energy_mwh: float = Field(0, description="Renewable energy")
    renewable_percentage: float = Field(0, ge=0, le=100)
    energy_intensity_value: Optional[float] = None
    energy_intensity_unit: Optional[str] = "MWh/million_EUR"
    by_source: Optional[Dict[str, float]] = Field(default_factory=dict)

class GHGBreakdown(BaseModel):
    """Detailed GHG breakdown by gas type"""
    CO2: float = Field(0, description="CO2 emissions in tonnes")
    CH4: float = Field(0, description="CH4 emissions in tonnes")
    N2O: float = Field(0, description="N2O emissions in tonnes")
    HFCs: Optional[float] = Field(0, description="HFCs in tonnes CO2e")
    PFCs: Optional[float] = Field(0, description="PFCs in tonnes CO2e")
    SF6: Optional[float] = Field(0, description="SF6 in tonnes")
    NF3: Optional[float] = Field(0, description="NF3 in tonnes")
    total_co2e: float = Field(..., description="Total CO2 equivalent")
    gwp_version: str = Field("AR6", description="GWP version used")

class InternalCarbonPricing(BaseModel):
    """E1-8: Internal carbon pricing"""
    implemented: bool = Field(False)
    price_per_tco2e: Optional[float] = None
    currency: str = Field("EUR")
    coverage_scope1: bool = Field(False)
    coverage_scope2: bool = Field(False)
    coverage_scope3_categories: List[int] = Field(default_factory=list)
    pricing_type: Optional[str] = Field(None, description="shadow/internal/implicit")
    revenue_generated: Optional[float] = Field(0)
    revenue_allocation: Optional[str] = None

class ClimatePolicy(BaseModel):
    """E1-2: Climate policies"""
    has_climate_policy: bool = Field(False)
    policy_adoption_date: Optional[date] = None
    policy_url: Optional[str] = None
    net_zero_target_year: Optional[int] = None
    interim_targets: List[Dict[str, any]] = Field(default_factory=list)
    board_oversight: bool = Field(False)
    executive_compensation_linked: bool = Field(False)

class ClimateActions(BaseModel):
    """E1-3: Actions and resources"""
    reporting_year: int
    capex_climate_eur: float = Field(0, description="CapEx for climate actions")
    opex_climate_eur: float = Field(0, description="OpEx for climate actions")
    fte_dedicated: float = Field(0, description="FTEs dedicated to climate")
    key_projects: List[Dict[str, any]] = Field(default_factory=list)

class ESRSE1Metadata(BaseModel):
    """Complete ESRS E1 metadata structure"""
    energy_consumption: Optional[EnergyConsumption] = None
    ghg_breakdown: Optional[GHGBreakdown] = None
    internal_carbon_pricing: Optional[InternalCarbonPricing] = None
    climate_policy: Optional[ClimatePolicy] = None
    climate_actions: Optional[ClimateActions] = None