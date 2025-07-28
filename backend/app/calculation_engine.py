# backend/app/calculation_engine.py
"""
GHG Protocol Calculation Engine
Implements comprehensive emissions calculations following GHG Protocol standards
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import date, datetime
from dataclasses import dataclass, field
import logging
import math
from enum import Enum

from .api_models import (
    EmissionScope, ActivityType, CalculationMethod, 
    DataQuality, ActivityDataRequest
)

logger = logging.getLogger(__name__)

# Global Warming Potential values (AR5 100-year)
GWP_VALUES = {
    "CO2": Decimal("1"),
    "CH4": Decimal("28"),
    "N2O": Decimal("265"),
    "HFC-134a": Decimal("1430"),
    "HFC-23": Decimal("14800"),
    "SF6": Decimal("22800"),
    "PFC-14": Decimal("7390"),
}

# Unit conversion factors to base units
UNIT_CONVERSIONS = {
    # Energy
    "kWh": Decimal("1"),
    "MWh": Decimal("1000"),
    "GJ": Decimal("277.778"),  # to kWh
    "MMBtu": Decimal("293.071"),  # to kWh
    
    # Volume
    "liters": Decimal("1"),
    "gallons": Decimal("3.78541"),  # to liters
    "m3": Decimal("1000"),  # to liters
    
    # Mass
    "kg": Decimal("1"),
    "tonnes": Decimal("1000"),
    "tons": Decimal("907.185"),  # short tons to kg
    "lbs": Decimal("0.453592"),  # to kg
    
    # Distance
    "km": Decimal("1"),
    "miles": Decimal("1.60934"),  # to km
}

@dataclass
class EmissionFactor:
    """Emission factor with metadata"""
    factor: Decimal  # kgCO2e per unit
    unit: str
    scope: EmissionScope
    source: str
    uncertainty: Decimal = Decimal("0.05")  # 5% default
    year: int = 2024
    region: Optional[str] = None
    gas_breakdown: Dict[str, Decimal] = field(default_factory=dict)

@dataclass
class CalculationResult:
    """Result of an emission calculation"""
    emissions_co2e: Decimal
    scope: EmissionScope
    activity_type: ActivityType
    calculation_method: CalculationMethod
    data_quality_score: float
    uncertainty_range: Tuple[Decimal, Decimal]
    gas_breakdown: Dict[str, Decimal]
    metadata: Dict[str, Any]

@dataclass
class AggregatedResults:
    """Aggregated emission results"""
    total_emissions: Decimal
    scope1_emissions: Decimal
    scope2_emissions: Decimal
    scope3_emissions: Decimal
    emissions_by_category: Dict[str, Decimal]
    emissions_by_gas: Dict[str, Decimal]
    data_quality_score: float
    uncertainty_range: Tuple[Decimal, Decimal]
    calculation_details: List[CalculationResult]

class UncertaintyCalculator:
    """Calculate uncertainty following GHG Protocol guidance"""
    
    @staticmethod
    def calculate_combined_uncertainty(uncertainties: List[float]) -> float:
        """
        Calculate combined uncertainty using root sum of squares
        GHG Protocol Equation 7.2
        """
        if not uncertainties:
            return 0.0
        
        sum_of_squares = sum(u ** 2 for u in uncertainties)
        return math.sqrt(sum_of_squares)
    
    @staticmethod
    def calculate_weighted_uncertainty(
        values: List[Decimal], 
        uncertainties: List[float]
    ) -> float:
        """
        Calculate weighted uncertainty for aggregated values
        """
        if not values or not uncertainties:
            return 0.0
        
        total = sum(values)
        if total == 0:
            return 0.0
        
        weighted_sum = sum(
            (val / total) ** 2 * unc ** 2 
            for val, unc in zip(values, uncertainties)
        )
        return math.sqrt(weighted_sum)

class DataQualityAssessor:
    """Assess data quality following GHG Protocol guidance"""
    
    QUALITY_SCORES = {
        DataQuality.PRIMARY: 1.0,
        DataQuality.SECONDARY: 0.75,
        DataQuality.ESTIMATED: 0.5,
        DataQuality.PROXY: 0.25,
    }
    
    @classmethod
    def calculate_score(
        cls, 
        data_quality: DataQuality,
        temporal_correlation: float = 1.0,  # 0-1, how recent
        geographical_correlation: float = 1.0,  # 0-1, how specific
        technological_correlation: float = 1.0  # 0-1, how relevant
    ) -> float:
        """
        Calculate data quality score based on GHG Protocol criteria
        """
        base_score = cls.QUALITY_SCORES[data_quality]
        
        # Apply correlation factors
        correlation_factor = (
            temporal_correlation * 0.3 +
            geographical_correlation * 0.3 +
            technological_correlation * 0.4
        )
        
        return base_score * correlation_factor

class GHGCalculationEngine:
    """
    Main calculation engine implementing GHG Protocol methodologies
    """
    
    def __init__(self):
        self.uncertainty_calculator = UncertaintyCalculator()
        self.quality_assessor = DataQualityAssessor()
        self._load_default_factors()
    
    def _load_default_factors(self):
        """Load default emission factors"""
        self.default_factors = {
            # Scope 1 - Direct emissions
            ActivityType.FUEL_COMBUSTION: {
                "natural_gas": EmissionFactor(
                    factor=Decimal("1.85"),  # kg CO2e/m3
                    unit="m3",
                    scope=EmissionScope.SCOPE_1,
                    source="EPA Emission Factors Hub",
                    gas_breakdown={"CO2": Decimal("1.85"), "CH4": Decimal("0.001"), "N2O": Decimal("0.0001")}
                ),
                "diesel": EmissionFactor(
                    factor=Decimal("2.68"),  # kg CO2e/liter
                    unit="liters",
                    scope=EmissionScope.SCOPE_1,
                    source="GHG Protocol",
                    gas_breakdown={"CO2": Decimal("2.68"), "CH4": Decimal("0.0003"), "N2O": Decimal("0.0001")}
                ),
                "gasoline": EmissionFactor(
                    factor=Decimal("2.35"),  # kg CO2e/liter
                    unit="liters",
                    scope=EmissionScope.SCOPE_1,
                    source="GHG Protocol",
                    gas_breakdown={"CO2": Decimal("2.35"), "CH4": Decimal("0.0003"), "N2O": Decimal("0.0001")}
                ),
            },
            
            # Scope 2 - Indirect emissions from electricity
            ActivityType.ELECTRICITY: {
                "grid": EmissionFactor(
                    factor=Decimal("0.45"),  # kg CO2e/kWh (global average)
                    unit="kWh",
                    scope=EmissionScope.SCOPE_2,
                    source="IEA Global Average",
                    uncertainty=Decimal("0.10"),
                    gas_breakdown={"CO2": Decimal("0.45")}
                ),
                "renewable": EmissionFactor(
                    factor=Decimal("0.01"),  # kg CO2e/kWh
                    unit="kWh",
                    scope=EmissionScope.SCOPE_2,
                    source="LCA Studies",
                    gas_breakdown={"CO2": Decimal("0.01")}
                ),
            },
            
            # Scope 3 - Value chain emissions
            ActivityType.BUSINESS_TRAVEL: {
                "air_short": EmissionFactor(
                    factor=Decimal("0.255"),  # kg CO2e/passenger-km
                    unit="km",
                    scope=EmissionScope.SCOPE_3,
                    source="DEFRA 2024",
                    gas_breakdown={"CO2": Decimal("0.255")}
                ),
                "air_long": EmissionFactor(
                    factor=Decimal("0.195"),  # kg CO2e/passenger-km
                    unit="km",
                    scope=EmissionScope.SCOPE_3,
                    source="DEFRA 2024",
                    gas_breakdown={"CO2": Decimal("0.195")}
                ),
                "rail": EmissionFactor(
                    factor=Decimal("0.041"),  # kg CO2e/passenger-km
                    unit="km",
                    scope=EmissionScope.SCOPE_3,
                    source="DEFRA 2024",
                    gas_breakdown={"CO2": Decimal("0.041")}
                ),
            },
            
            ActivityType.WASTE: {
                "landfill": EmissionFactor(
                    factor=Decimal("467"),  # kg CO2e/tonne
                    unit="tonnes",
                    scope=EmissionScope.SCOPE_3,
                    source="EPA WARM",
                    uncertainty=Decimal("0.20"),
                    gas_breakdown={"CH4": Decimal("16.68"), "CO2": Decimal("0")}  # 467/28 = 16.68 kg CH4
                ),
                "recycling": EmissionFactor(
                    factor=Decimal("-885"),  # kg CO2e/tonne (negative = avoided)
                    unit="tonnes",
                    scope=EmissionScope.SCOPE_3,
                    source="EPA WARM",
                    gas_breakdown={"CO2": Decimal("-885")}
                ),
            },
        }
    
    def calculate_emissions(
        self,
        activity_data: List[ActivityDataRequest],
        custom_factors: Optional[Dict[str, EmissionFactor]] = None,
        method: CalculationMethod = CalculationMethod.ACTIVITY_BASED
    ) -> AggregatedResults:
        """
        Calculate emissions for a list of activities
        """
        results = []
        emissions_by_scope = {
            EmissionScope.SCOPE_1: Decimal("0"),
            EmissionScope.SCOPE_2: Decimal("0"),
            EmissionScope.SCOPE_3: Decimal("0"),
        }
        emissions_by_category = {}
        emissions_by_gas = {}
        
        for activity in activity_data:
            result = self._calculate_single_activity(
                activity, custom_factors, method
            )
            results.append(result)
            
            # Aggregate by scope
            emissions_by_scope[result.scope] += result.emissions_co2e
            
            # Aggregate by category
            if activity.activity_type not in emissions_by_category:
                emissions_by_category[activity.activity_type] = Decimal("0")
            emissions_by_category[activity.activity_type] += result.emissions_co2e
            
            # Aggregate by gas
            for gas, amount in result.gas_breakdown.items():
                if gas not in emissions_by_gas:
                    emissions_by_gas[gas] = Decimal("0")
                emissions_by_gas[gas] += amount
        
        # Calculate total emissions
        total_emissions = sum(emissions_by_scope.values())
        
        # Calculate overall data quality
        quality_scores = [r.data_quality_score for r in results]
        emissions_values = [r.emissions_co2e for r in results]
        
        weighted_quality = sum(
            q * e for q, e in zip(quality_scores, emissions_values)
        ) / total_emissions if total_emissions > 0 else 0
        
        # Calculate overall uncertainty
        uncertainties = [
            (r.uncertainty_range[1] - r.uncertainty_range[0]) / (2 * r.emissions_co2e) 
            if r.emissions_co2e > 0 else 0
            for r in results
        ]
        overall_uncertainty = self.uncertainty_calculator.calculate_weighted_uncertainty(
            emissions_values, uncertainties
        )
        
        uncertainty_range = (
            total_emissions * (1 - overall_uncertainty),
            total_emissions * (1 + overall_uncertainty)
        )
        
        return AggregatedResults(
            total_emissions=total_emissions,
            scope1_emissions=emissions_by_scope[EmissionScope.SCOPE_1],
            scope2_emissions=emissions_by_scope[EmissionScope.SCOPE_2],
            scope3_emissions=emissions_by_scope[EmissionScope.SCOPE_3],
            emissions_by_category={k.value: v for k, v in emissions_by_category.items()},
            emissions_by_gas=emissions_by_gas,
            data_quality_score=weighted_quality,
            uncertainty_range=uncertainty_range,
            calculation_details=results
        )
    
    def _calculate_single_activity(
        self,
        activity: ActivityDataRequest,
        custom_factors: Optional[Dict[str, EmissionFactor]],
        method: CalculationMethod
    ) -> CalculationResult:
        """
        Calculate emissions for a single activity
        """
        # Get emission factor
        factor = self._get_emission_factor(activity, custom_factors)
        
        # Convert units if necessary
        quantity = self._convert_units(
            activity.quantity, 
            activity.unit, 
            factor.unit
        )
        
        # Calculate base emissions
        emissions_co2e = quantity * factor.factor
        
        # Calculate gas breakdown
        gas_breakdown = {}
        for gas, gas_factor in factor.gas_breakdown.items():
            gas_amount = quantity * gas_factor
            gas_breakdown[gas] = gas_amount
        
        # Assess data quality
        quality_score = self.quality_assessor.calculate_score(
            activity.data_quality,
            temporal_correlation=self._assess_temporal_correlation(activity, factor),
            geographical_correlation=0.9,  # Could be enhanced with location matching
            technological_correlation=1.0
        )
        
        # Calculate uncertainty
        base_uncertainty = float(factor.uncertainty)
        data_quality_uncertainty = (1 - quality_score) * 0.2  # up to 20% additional
        total_uncertainty = self.uncertainty_calculator.calculate_combined_uncertainty(
            [base_uncertainty, data_quality_uncertainty]
        )
        
        uncertainty_range = (
            emissions_co2e * Decimal(1 - total_uncertainty),
            emissions_co2e * Decimal(1 + total_uncertainty)
        )
        
        return CalculationResult(
            emissions_co2e=emissions_co2e.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            scope=factor.scope,
            activity_type=activity.activity_type,
            calculation_method=method,
            data_quality_score=quality_score,
            uncertainty_range=uncertainty_range,
            gas_breakdown=gas_breakdown,
            metadata={
                "factor_source": factor.source,
                "factor_year": factor.year,
                "quantity": float(quantity),
                "unit": factor.unit,
                "original_unit": activity.unit
            }
        )
    
    def _get_emission_factor(
        self,
        activity: ActivityDataRequest,
        custom_factors: Optional[Dict[str, EmissionFactor]]
    ) -> EmissionFactor:
        """
        Get emission factor for an activity
        """
        # Check custom factors first
        if custom_factors and activity.activity_type.value in custom_factors:
            return custom_factors[activity.activity_type.value]
        
        # Use default factors
        activity_factors = self.default_factors.get(activity.activity_type, {})
        
        # Simple matching - in production, this would be more sophisticated
        if activity.description and "renewable" in activity.description.lower():
            factor_key = "renewable"
        elif activity.description:
            # Try to match description to factor keys
            for key in activity_factors.keys():
                if key in activity.description.lower():
                    factor_key = key
                    break
            else:
                factor_key = list(activity_factors.keys())[0] if activity_factors else None
        else:
            factor_key = list(activity_factors.keys())[0] if activity_factors else None
        
        if not factor_key or factor_key not in activity_factors:
            # Return a default factor if nothing matches
            return EmissionFactor(
                factor=Decimal("1.0"),
                unit=activity.unit,
                scope=EmissionScope.SCOPE_3,
                source="Default",
                uncertainty=Decimal("0.50"),  # High uncertainty
                gas_breakdown={"CO2": Decimal("1.0")}
            )
        
        return activity_factors[factor_key]
    
    def _convert_units(
        self, 
        quantity: float, 
        from_unit: str, 
        to_unit: str
    ) -> Decimal:
        """
        Convert between units
        """
        if from_unit == to_unit:
            return Decimal(str(quantity))
        
        # Get conversion factors
        from_factor = UNIT_CONVERSIONS.get(from_unit, Decimal("1"))
        to_factor = UNIT_CONVERSIONS.get(to_unit, Decimal("1"))
        
        # Convert to base unit then to target unit
        base_quantity = Decimal(str(quantity)) * from_factor
        return base_quantity / to_factor
    
    def _assess_temporal_correlation(
        self,
        activity: ActivityDataRequest,
        factor: EmissionFactor
    ) -> float:
        """
        Assess how well the factor year matches the activity period
        """
        activity_year = activity.start_date.year
        factor_year = factor.year
        
        year_diff = abs(activity_year - factor_year)
        
        if year_diff == 0:
            return 1.0
        elif year_diff <= 2:
            return 0.9
        elif year_diff <= 5:
            return 0.7
        else:
            return 0.5
    
    def validate_activity_data(
        self,
        activity_data: List[ActivityDataRequest]
    ) -> Tuple[bool, List[str]]:
        """
        Validate activity data before calculation
        """
        errors = []
        
        for i, activity in enumerate(activity_data):
            # Check quantity
            if activity.quantity <= 0:
                errors.append(f"Activity {i}: Quantity must be positive")
            
            # Check dates
            if activity.end_date < activity.start_date:
                errors.append(f"Activity {i}: End date before start date")
            
            # Check unit validity
            if activity.unit not in UNIT_CONVERSIONS:
                logger.warning(f"Unknown unit: {activity.unit}")
        
        return len(errors) == 0, errors

# Convenience functions for direct use
def calculate_scope1_emissions(
    fuel_data: List[Dict[str, Any]]
) -> Decimal:
    """Calculate Scope 1 emissions from fuel combustion"""
    engine = GHGCalculationEngine()
    activities = [
        ActivityDataRequest(
            activity_type=ActivityType.FUEL_COMBUSTION,
            quantity=data["quantity"],
            unit=data["unit"],
            start_date=date.today(),
            end_date=date.today(),
            data_quality=DataQuality.PRIMARY,
            description=data.get("fuel_type", "")
        )
        for data in fuel_data
    ]
    result = engine.calculate_emissions(activities)
    return result.scope1_emissions

def calculate_scope2_emissions(
    electricity_data: List[Dict[str, Any]],
    location_based: bool = True
) -> Decimal:
    """Calculate Scope 2 emissions from electricity"""
    engine = GHGCalculationEngine()
    activities = [
        ActivityDataRequest(
            activity_type=ActivityType.ELECTRICITY,
            quantity=data["quantity"],
            unit=data.get("unit", "kWh"),
            start_date=date.today(),
            end_date=date.today(),
            data_quality=DataQuality.PRIMARY,
            description="grid" if location_based else data.get("source", "grid")
        )
        for data in electricity_data
    ]
    result = engine.calculate_emissions(activities)
    return result.scope2_emissions

def calculate_scope3_emissions(
    activity_data: List[Dict[str, Any]]
) -> Decimal:
    """Calculate Scope 3 emissions from various activities"""
    engine = GHGCalculationEngine()
    activities = []
    
    for data in activity_data:
        activity_type = ActivityType(data["activity_type"])
        activities.append(
            ActivityDataRequest(
                activity_type=activity_type,
                quantity=data["quantity"],
                unit=data["unit"],
                start_date=date.today(),
                end_date=date.today(),
                data_quality=DataQuality(data.get("data_quality", "secondary")),
                description=data.get("description", "")
            )
        )
    
    result = engine.calculate_emissions(activities)
    return result.scope3_emissions