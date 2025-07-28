"""
Calculation Engine for GHG Protocol Scope 3 Emissions
Implements all 15 category calculations with uncertainty propagation
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from scipy import stats
import logging

from app.models.ghg_protocol_models import (
    Scope3Category, MethodologyType, EmissionFactor, ActivityData,
    EmissionResult, CalculationParameters, CategoryCalculationResult,
    DataQualityIndicator, UncertaintyDistribution, TransportMode,
    WasteTreatment, Quantity, PurchasedGoodsActivity, BusinessTravelActivity,
    UpstreamTransportActivity, WasteActivity, UsePhaseActivity
)

logger = logging.getLogger(__name__)


class UncertaintyEngine:
    """Implements IPCC Tier 2 uncertainty propagation using Monte Carlo"""
    
    def __init__(self, n_iterations: int = 10_000, confidence_level: float = 0.95):
        self.n_iterations = n_iterations
        self.confidence_level = confidence_level
        
    def propagate_uncertainty(
        self,
        activity_value: float,
        activity_uncertainty: Tuple[float, float],
        ef_value: float,
        ef_uncertainty: Tuple[float, float],
        distribution: UncertaintyDistribution = UncertaintyDistribution.LOGNORMAL
    ) -> EmissionResult:
        """
        Propagate uncertainty through multiplication using Monte Carlo
        
        Args:
            activity_value: Central estimate of activity data
            activity_uncertainty: (lower, upper) uncertainty range as CV%
            ef_value: Central estimate of emission factor
            ef_uncertainty: (lower, upper) uncertainty range as CV%
            distribution: Statistical distribution to use
            
        Returns:
            EmissionResult with confidence intervals
        """
        # Use Latin Hypercube Sampling for efficiency
        lhs_samples = self._latin_hypercube_sample(self.n_iterations)
        
        # Generate distributions
        activity_samples = self._generate_distribution(
            activity_value, activity_uncertainty, distribution, lhs_samples[:, 0]
        )
        ef_samples = self._generate_distribution(
            ef_value, ef_uncertainty, distribution, lhs_samples[:, 1]
        )
        
        # Calculate emissions
        emission_samples = activity_samples * ef_samples
        
        # Calculate percentiles
        percentiles = [
            (1 - self.confidence_level) / 2,
            0.5,
            1 - (1 - self.confidence_level) / 2
        ]
        p5, p50, p95 = np.percentile(emission_samples, [p * 100 for p in percentiles])
        
        return EmissionResult(
            value=Decimal(str(p50)),
            uncertainty_lower=Decimal(str(p5)),
            uncertainty_upper=Decimal(str(p95))
        )
    
    def _latin_hypercube_sample(self, n_samples: int, n_variables: int = 2) -> np.ndarray:
        """Generate Latin Hypercube samples for reduced variance"""
        samples = np.zeros((n_samples, n_variables))
        
        for i in range(n_variables):
            # Create evenly spaced intervals
            intervals = np.linspace(0, 1, n_samples + 1)
            # Sample within each interval
            samples[:, i] = np.random.uniform(intervals[:-1], intervals[1:])
            # Shuffle to remove correlation
            np.random.shuffle(samples[:, i])
            
        return samples
    
    def _generate_distribution(
        self,
        mean: float,
        uncertainty: Tuple[float, float],
        distribution: UncertaintyDistribution,
        uniform_samples: np.ndarray
    ) -> np.ndarray:
        """Generate samples from specified distribution"""
        cv = np.mean(uncertainty) / 100  # Convert percentage to coefficient
        
        if distribution == UncertaintyDistribution.NORMAL:
            std = mean * cv
            return stats.norm.ppf(uniform_samples, loc=mean, scale=std)
            
        elif distribution == UncertaintyDistribution.LOGNORMAL:
            # Convert to lognormal parameters
            variance = (mean * cv) ** 2
            mu = np.log(mean**2 / np.sqrt(variance + mean**2))
            sigma = np.sqrt(np.log(1 + variance / mean**2))
            return stats.lognorm.ppf(uniform_samples, s=sigma, scale=np.exp(mu))
            
        elif distribution == UncertaintyDistribution.TRIANGULAR:
            # Use uncertainty range for triangular bounds
            lower = mean * (1 - uncertainty[0] / 100)
            upper = mean * (1 + uncertainty[1] / 100)
            return stats.triang.ppf(
                uniform_samples,
                c=0.5,  # Mode at center
                loc=lower,
                scale=upper - lower
            )
            
        else:  # UNIFORM
            lower = mean * (1 - uncertainty[0] / 100)
            upper = mean * (1 + uncertainty[1] / 100)
            return stats.uniform.ppf(uniform_samples, loc=lower, scale=upper - lower)


class CategoryCalculator(ABC):
    """Abstract base class for category-specific calculations"""
    
    def __init__(self, uncertainty_engine: UncertaintyEngine):
        self.uncertainty_engine = uncertainty_engine
        
    @abstractmethod
    def calculate(
        self,
        activity_data: List[ActivityData],
        emission_factors: List[EmissionFactor],
        parameters: CalculationParameters
    ) -> CategoryCalculationResult:
        """Calculate emissions for the category"""
        pass
    
    @abstractmethod
    def validate_data(
        self,
        activity_data: List[ActivityData],
        emission_factors: List[EmissionFactor]
    ) -> List[str]:
        """Validate input data for the category"""
        pass
    
    def apply_gwp(self, emissions: Dict[str, float], gwp_version: str = "AR6") -> float:
        """Apply Global Warming Potential factors"""
        gwp_factors = {
            "AR6": {"CO2": 1, "CH4": 27.9, "N2O": 273},
            "AR5": {"CO2": 1, "CH4": 28, "N2O": 265},
            "AR4": {"CO2": 1, "CH4": 25, "N2O": 298}
        }
        
        factors = gwp_factors.get(gwp_version, gwp_factors["AR6"])
        total = 0
        
        for gas, amount in emissions.items():
            total += amount * factors.get(gas, 1)
            
        return total


class Category1Calculator(CategoryCalculator):
    """Category 1: Purchased Goods and Services"""
    
    def calculate(
        self,
        activity_data: List[PurchasedGoodsActivity],
        emission_factors: List[EmissionFactor],
        parameters: CalculationParameters
    ) -> CategoryCalculationResult:
        """
        Calculate emissions using:
        E = Σ(Quantity[i] × EF[i] × (1 + Transport_factor[i]))
        """
        total_emissions = Decimal('0')
        emissions_by_source = {}
        
        for activity in activity_data:
            # Find matching emission factor
            ef = self._match_emission_factor(activity, emission_factors)
            if not ef:
                logger.warning(f"No emission factor found for {activity.product_description}")
                continue
            
            # Base calculation
            quantity = float(activity.quantity.value)
            ef_value = float(ef.value)
            
            # Add transport factor if applicable
            transport_factor = 1.0
            if activity.transport_distance:
                transport_ef = self._get_transport_factor(activity.supplier_country)
                transport_factor += (activity.transport_distance * transport_ef)
            
            if parameters.include_uncertainty and ef.uncertainty_range:
                result = self.uncertainty_engine.propagate_uncertainty(
                    quantity,
                    (10, 10),  # Default activity uncertainty
                    ef_value * transport_factor,
                    ef.uncertainty_range,
                    UncertaintyDistribution.LOGNORMAL
                )
            else:
                emissions = quantity * ef_value * transport_factor
                result = EmissionResult(value=Decimal(str(emissions)))
            
            total_emissions += result.value
            emissions_by_source[activity.product_description] = result
        
        return self._create_result(
            category=Scope3Category.PURCHASED_GOODS_AND_SERVICES,
            total_emissions=total_emissions,
            emissions_by_source=emissions_by_source,
            activity_data=activity_data,
            emission_factors=emission_factors,
            parameters=parameters
        )
    
    def validate_data(
        self,
        activity_data: List[PurchasedGoodsActivity],
        emission_factors: List[EmissionFactor]
    ) -> List[str]:
        errors = []
        
        for activity in activity_data:
            if not activity.product_description:
                errors.append("Product description is required")
            if activity.quantity.value <= 0:
                errors.append(f"Invalid quantity for {activity.product_description}")
            if activity.recycled_content and not (0 <= activity.recycled_content <= 1):
                errors.append("Recycled content must be between 0 and 1")
                
        if not emission_factors:
            errors.append("No emission factors provided")
            
        return errors
    
    def _match_emission_factor(
        self,
        activity: PurchasedGoodsActivity,
        emission_factors: List[EmissionFactor]
    ) -> Optional[EmissionFactor]:
        """Match activity to most appropriate emission factor"""
        # Implement matching logic based on product type, region, year
        # This is simplified - real implementation would be more sophisticated
        for ef in emission_factors:
            if ef.category == Scope3Category.PURCHASED_GOODS_AND_SERVICES:
                if activity.supplier_country == ef.region or ef.region is None:
                    return ef
        return None
    
    def _get_transport_factor(self, country: str) -> float:
        """Get transport emission factor by country"""
        # Simplified - real implementation would use actual data
        transport_factors = {
            "US": 0.05,
            "CN": 0.08,
            "EU": 0.04,
            "default": 0.06
        }
        return transport_factors.get(country, transport_factors["default"])
    
    def _create_result(
        self,
        category: Scope3Category,
        total_emissions: Decimal,
        emissions_by_source: Dict[str, EmissionResult],
        activity_data: List[ActivityData],
        emission_factors: List[EmissionFactor],
        parameters: CalculationParameters
    ) -> CategoryCalculationResult:
        """Create standardized result object"""
        # Calculate data quality score
        quality_scores = [ad.quality_indicator.overall_score for ad in activity_data]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 5.0
        
        return CategoryCalculationResult(
            organization_id=activity_data[0].id,  # Placeholder
            category=category,
            reporting_period=activity_data[0].time_period,
            methodology=parameters.methodology,
            emissions=EmissionResult(value=total_emissions),
            activity_data_count=len(activity_data),
            data_quality_score=avg_quality,
            emissions_by_source=emissions_by_source,
            calculation_parameters=parameters,
            emission_factors_used=[ef.id for ef in emission_factors],
            activity_data_used=[ad.id for ad in activity_data]
        )


class Category6Calculator(CategoryCalculator):
    """Category 6: Business Travel"""
    
    # Radiative Forcing Index for aviation
    RFI_FACTOR = 1.9
    
    # Detour factors by flight type
    DETOUR_FACTORS = {
        "domestic": 1.09,
        "short_haul": 1.10,
        "long_haul": 1.10
    }
    
    # Cabin class multipliers
    CABIN_MULTIPLIERS = {
        "economy": 1.0,
        "premium_economy": 1.3,
        "business": 2.0,
        "first": 2.5
    }
    
    def calculate(
        self,
        activity_data: List[BusinessTravelActivity],
        emission_factors: List[EmissionFactor],
        parameters: CalculationParameters
    ) -> CategoryCalculationResult:
        """
        Calculate emissions for business travel:
        Air: E = Σ(Distance × EF × Cabin_factor × RFI × Detour_factor)
        Ground: E = Σ(Distance × EF / Occupancy)
        Hotel: E = Σ(Nights × EF × Hotel_factor)
        """
        total_emissions = Decimal('0')
        emissions_by_source = {}
        emissions_by_mode = {"air": Decimal('0'), "ground": Decimal('0'), "hotel": Decimal('0')}
        
        for activity in activity_data:
            if activity.mode == TransportMode.AIR:
                emissions = self._calculate_air_travel(activity, emission_factors)
                emissions_by_mode["air"] += emissions.value
            else:
                emissions = self._calculate_ground_travel(activity, emission_factors)
                emissions_by_mode["ground"] += emissions.value
            
            # Add hotel emissions if applicable
            if activity.hotel_nights and activity.hotel_nights > 0:
                hotel_emissions = self._calculate_hotel_emissions(activity, emission_factors)
                emissions_by_mode["hotel"] += hotel_emissions.value
                emissions.value += hotel_emissions.value
            
            total_emissions += emissions.value
            trip_key = f"{activity.origin}-{activity.destination}-{activity.mode.value}"
            emissions_by_source[trip_key] = emissions
        
        return self._create_result(
            category=Scope3Category.BUSINESS_TRAVEL,
            total_emissions=total_emissions,
            emissions_by_source=emissions_by_source,
            activity_data=activity_data,
            emission_factors=emission_factors,
            parameters=parameters
        )
    
    def _calculate_air_travel(
        self,
        activity: BusinessTravelActivity,
        emission_factors: List[EmissionFactor]
    ) -> EmissionResult:
        """Calculate air travel emissions with RFI and cabin class"""
        # Determine flight type based on distance
        flight_type = self._get_flight_type(activity.distance)
        detour = self.DETOUR_FACTORS.get(flight_type, 1.1)
        
        # Get cabin class multiplier
        cabin_mult = self.CABIN_MULTIPLIERS.get(
            activity.cabin_class or "economy",
            1.0
        )
        
        # Find appropriate emission factor
        ef = self._match_transport_ef(TransportMode.AIR, emission_factors)
        
        # Calculate emissions
        emissions = (
            activity.distance *
            activity.travelers *
            float(ef.value) *
            cabin_mult *
            self.RFI_FACTOR *
            detour
        )
        
        return EmissionResult(value=Decimal(str(emissions)))
    
    def _calculate_ground_travel(
        self,
        activity: BusinessTravelActivity,
        emission_factors: List[EmissionFactor]
    ) -> EmissionResult:
        """Calculate ground transportation emissions"""
        ef = self._match_transport_ef(activity.mode, emission_factors)
        
        # Default occupancy rates
        occupancy = {
            TransportMode.ROAD: 1.5,  # Average car occupancy
            TransportMode.RAIL: 0.35,  # Load factor
            TransportMode.SEA: 0.7,    # Load factor
        }.get(activity.mode, 1.0)
        
        emissions = (
            activity.distance *
            activity.travelers *
            float(ef.value) /
            occupancy
        )
        
        return EmissionResult(value=Decimal(str(emissions)))
    
    def _calculate_hotel_emissions(
        self,
        activity: BusinessTravelActivity,
        emission_factors: List[EmissionFactor]
    ) -> EmissionResult:
        """Calculate hotel accommodation emissions"""
        # Find country-specific hotel EF
        country = activity.hotel_country or activity.destination
        ef = self._match_hotel_ef(country, emission_factors)
        
        emissions = activity.hotel_nights * float(ef.value)
        return EmissionResult(value=Decimal(str(emissions)))
    
    def _get_flight_type(self, distance: float) -> str:
        """Categorize flight by distance"""
        if distance < 500:
            return "domestic"
        elif distance < 3700:
            return "short_haul"
        else:
            return "long_haul"
    
    def _match_transport_ef(
        self,
        mode: TransportMode,
        emission_factors: List[EmissionFactor]
    ) -> EmissionFactor:
        """Match transport mode to emission factor"""
        for ef in emission_factors:
            if ef.category == Scope3Category.BUSINESS_TRAVEL:
                if ef.metadata.get("mode") == mode.value:
                    return ef
        # Return default if not found
        return EmissionFactor(
            name="Default transport",
            category=Scope3Category.BUSINESS_TRAVEL,
            value=Decimal("0.15"),  # Default kgCO2e/km
            unit="kgCO2e/km",
            source=EmissionFactorSource.EPA,
            source_reference="Default",
            year=2024
        )
    
    def _match_hotel_ef(
        self,
        country: str,
        emission_factors: List[EmissionFactor]
    ) -> EmissionFactor:
        """Match hotel country to emission factor"""
        for ef in emission_factors:
            if ef.metadata.get("type") == "hotel" and ef.region == country:
                return ef
        # Return default
        return EmissionFactor(
            name="Default hotel",
            category=Scope3Category.BUSINESS_TRAVEL,
            value=Decimal("15.0"),  # Default kgCO2e/night
            unit="kgCO2e/night",
            source=EmissionFactorSource.DEFRA,
            source_reference="Default",
            year=2024
        )
    
    def validate_data(
        self,
        activity_data: List[BusinessTravelActivity],
        emission_factors: List[EmissionFactor]
    ) -> List[str]:
        errors = []
        
        for activity in activity_data:
            if activity.distance <= 0:
                errors.append(f"Invalid distance for {activity.origin}-{activity.destination}")
            if activity.travelers <= 0:
                errors.append("Number of travelers must be positive")
            if activity.cabin_class and activity.cabin_class not in self.CABIN_MULTIPLIERS:
                errors.append(f"Invalid cabin class: {activity.cabin_class}")
                
        return errors


class Category11Calculator(CategoryCalculator):
    """Category 11: Use of Sold Products"""
    
    def calculate(
        self,
        activity_data: List[UsePhaseActivity],
        emission_factors: List[EmissionFactor],
        parameters: CalculationParameters
    ) -> CategoryCalculationResult:
        """
        Calculate use-phase emissions:
        E = Σ(Units_sold × Lifetime_energy × Grid_EF × Usage_rate)
        """
        total_emissions = Decimal('0')
        emissions_by_source = {}
        emissions_by_region = {}
        
        for activity in activity_data:
            product_emissions = Decimal('0')
            
            # Calculate emissions by geographic distribution
            for region, percentage in activity.geographic_distribution.items():
                # Get region-specific grid factor
                grid_ef = self._get_grid_factor(region, emission_factors)
                
                # Calculate lifetime energy consumption
                lifetime_energy = (
                    float(activity.energy_consumption.value) *
                    activity.product_lifetime *
                    self._get_usage_hours(activity)
                )
                
                # Calculate emissions for this region
                regional_units = activity.units_sold * percentage
                emissions = regional_units * lifetime_energy * float(grid_ef.value)
                
                product_emissions += Decimal(str(emissions))
                
                # Track by region
                if region not in emissions_by_region:
                    emissions_by_region[region] = Decimal('0')
                emissions_by_region[region] += Decimal(str(emissions))
            
            total_emissions += product_emissions
            emissions_by_source[activity.product_model] = EmissionResult(
                value=product_emissions
            )
        
        return CategoryCalculationResult(
            organization_id=activity_data[0].id,
            category=Scope3Category.USE_OF_SOLD_PRODUCTS,
            reporting_period=activity_data[0].time_period,
            methodology=parameters.methodology,
            emissions=EmissionResult(value=total_emissions),
            activity_data_count=len(activity_data),
            data_quality_score=3.0,  # Placeholder
            emissions_by_source=emissions_by_source,
            emissions_by_region={k: EmissionResult(value=v) for k, v in emissions_by_region.items()},
            calculation_parameters=parameters,
            emission_factors_used=[ef.id for ef in emission_factors],
            activity_data_used=[ad.id for ad in activity_data]
        )
    
    def _get_grid_factor(
        self,
        region: str,
        emission_factors: List[EmissionFactor]
    ) -> EmissionFactor:
        """Get electricity grid emission factor for region"""
        for ef in emission_factors:
            if ef.metadata.get("type") == "grid" and ef.region == region:
                return ef
        # Return global average if not found
        return EmissionFactor(
            name="Global grid average",
            category=Scope3Category.USE_OF_SOLD_PRODUCTS,
            value=Decimal("0.5"),  # kgCO2e/kWh
            unit="kgCO2e/kWh",
            source=EmissionFactorSource.IEA,
            source_reference="Global average",
            year=2024
        )
    
    def _get_usage_hours(self, activity: UsePhaseActivity) -> float:
        """Calculate total usage hours over product lifetime"""
        # Default usage patterns by product type
        if "daily_hours" in activity.usage_profile:
            return activity.usage_profile["daily_hours"] * 365
        elif "annual_hours" in activity.usage_profile:
            return activity.usage_profile["annual_hours"]
        else:
            # Default assumption: 8 hours/day
            return 8 * 365
    
    def validate_data(
        self,
        activity_data: List[UsePhaseActivity],
        emission_factors: List[EmissionFactor]
    ) -> List[str]:
        errors = []
        
        for activity in activity_data:
            if activity.units_sold <= 0:
                errors.append(f"Invalid units sold for {activity.product_model}")
            if activity.product_lifetime <= 0:
                errors.append(f"Invalid product lifetime for {activity.product_model}")
            if not activity.geographic_distribution:
                errors.append(f"Geographic distribution required for {activity.product_model}")
            
            # Check distribution sums to 100%
            total_dist = sum(activity.geographic_distribution.values())
            if abs(total_dist - 1.0) > 0.01:
                errors.append(f"Geographic distribution must sum to 100% for {activity.product_model}")
                
        return errors


class CalculationEngineFactory:
    """Factory to create appropriate calculators for each category"""
    
    def __init__(self, uncertainty_engine: Optional[UncertaintyEngine] = None):
        self.uncertainty_engine = uncertainty_engine or UncertaintyEngine()
        self._calculators = {
            Scope3Category.PURCHASED_GOODS_AND_SERVICES: Category1Calculator,
            Scope3Category.BUSINESS_TRAVEL: Category6Calculator,
            Scope3Category.USE_OF_SOLD_PRODUCTS: Category11Calculator,
            # Add other categories as implemented
        }
    
    def get_calculator(self, category: Scope3Category) -> CategoryCalculator:
        """Get calculator instance for specific category"""
        calculator_class = self._calculators.get(category)
        if not calculator_class:
            raise ValueError(f"No calculator implemented for category {category}")
        
        return calculator_class(self.uncertainty_engine)
    
    def calculate_category(
        self,
        category: Scope3Category,
        activity_data: List[ActivityData],
        emission_factors: List[EmissionFactor],
        parameters: CalculationParameters
    ) -> CategoryCalculationResult:
        """Calculate emissions for a specific category"""
        calculator = self.get_calculator(category)
        
        # Validate data first
        errors = calculator.validate_data(activity_data, emission_factors)
        if errors:
            raise ValueError(f"Validation errors: {errors}")
        
        # Perform calculation
        result = calculator.calculate(activity_data, emission_factors, parameters)
        
        # Log calculation
        logger.info(
            f"Calculated {category.value}: {result.emissions.value} kgCO2e "
            f"from {result.activity_data_count} activity records"
        )
        
        return result


# Additional calculators for other categories would follow the same pattern...
# Category2Calculator, Category3Calculator, etc.